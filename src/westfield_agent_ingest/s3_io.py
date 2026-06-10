"""
I/O contra el bucket de conocimiento.

ObjectStore es el protocolo que consumen pipeline/migrate/scaffold — los
tests inyectan un fake en memoria; producción usa S3Store (boto3).
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol, runtime_checkable

import boto3
from botocore.exceptions import ClientError

from westfield_agent_ingest.contracts import AgentConfigDoc

_NOT_FOUND_CODES = {"NoSuchKey", "404", "NoSuchBucket"}
_VERSION_RE = re.compile(r"/vector_store/v(\d+)/")


class ObjectNotFoundError(Exception):
    """El objeto pedido no existe en el storage."""


@runtime_checkable
class ObjectStore(Protocol):
    """Lectura/escritura/listado de objetos, relativo al bucket configurado."""

    @property
    def bucket(self) -> str: ...

    def get_bytes(self, key: str) -> bytes: ...
    def get_text(self, key: str) -> str: ...
    def put_bytes(self, key: str, data: bytes) -> None: ...
    def put_text(self, key: str, text: str) -> None: ...
    def list_keys(self, prefix: str) -> list[str]: ...
    def exists(self, key: str) -> bool: ...


class S3Store:
    """Implementación boto3 de ObjectStore."""

    def __init__(self, *, bucket: str, region: str | None = None) -> None:
        if not bucket:
            raise ValueError("bucket S3 ausente — revisar S3_BUCKET.")
        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    @property
    def bucket(self) -> str:
        return self._bucket

    def get_bytes(self, key: str) -> bytes:
        try:
            res = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as err:
            code = err.response.get("Error", {}).get("Code", "")
            if code in _NOT_FOUND_CODES:
                raise ObjectNotFoundError(f"s3://{self._bucket}/{key}") from err
            raise
        return res["Body"].read()

    def get_text(self, key: str) -> str:
        return self.get_bytes(key).decode("utf-8")

    def put_bytes(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    def put_text(self, key: str, text: str) -> None:
        self.put_bytes(key, text.encode("utf-8"))

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            keys.extend(item["Key"] for item in page.get("Contents", []))
        return keys

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as err:
            code = err.response.get("Error", {}).get("Code", "")
            if code in _NOT_FOUND_CODES:
                return False
            raise


# ----------------------------------------------------------- helpers de alto nivel


def put_json(store: ObjectStore, key: str, obj: Any) -> None:
    store.put_text(key, json.dumps(obj, ensure_ascii=False, indent=2))


def read_agent_config(store: ObjectStore, prefix: str, agent_id: str) -> AgentConfigDoc:
    """raises ObjectNotFoundError si el agente no tiene config.json."""
    raw = store.get_text(f"{prefix}/{agent_id}/config.json")
    return AgentConfigDoc.model_validate_json(raw)


def write_agent_config(
    store: ObjectStore, prefix: str, agent_id: str, config: AgentConfigDoc
) -> None:
    put_json(store, f"{prefix}/{agent_id}/config.json", config.model_dump())


def next_vector_store_version(store: ObjectStore, prefix: str, agent_id: str) -> str:
    """Devuelve la próxima versión libre (v1, v2, ...) — nunca sobreescribe."""
    keys = store.list_keys(f"{prefix}/{agent_id}/vector_store/")
    versions = {int(m.group(1)) for key in keys if (m := _VERSION_RE.search(f"/{key}"))}
    return f"v{max(versions) + 1}" if versions else "v1"
