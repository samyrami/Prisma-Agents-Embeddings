"""
Settings del servicio de ingesta — todo por env vars (+ .env local).

Las credenciales AWS las resuelve boto3 por su cadena estándar
(AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / perfil / rol IAM).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    s3_bucket: str
    aws_region: str
    s3_prefix: str
    openai_api_key: str | None
    openai_base_url: str
    embedding_model: str
    embedding_provider: str


def load_settings() -> Settings:
    return Settings(
        s3_bucket=os.getenv("S3_BUCKET", "westfield-agent-knowledge"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_prefix=os.getenv("S3_PREFIX", "agents"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_provider="openai",
    )
