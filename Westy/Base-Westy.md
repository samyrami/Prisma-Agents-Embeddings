# Informe de Investigación: Crear Agentes de IA con Google Gemini Gems
### (Base para un documento de conocimiento RAG bilingüe + un prompt de sistema para un agente "creador de agentes")

## TL;DR
- En 2026, cualquier persona con una cuenta Google **gratuita** puede crear "Gems" (asistentes personalizados de Gemini) en gemini.google.com; los planes de pago (Google AI Pro/Ultra, Workspace) solo añaden **límites de uso más altos, ventana de contexto mayor y subidas más grandes**, no la capacidad de crear Gems.
- Un Gem combina **instrucciones persistentes + hasta 10 archivos de conocimiento (máx. 100 MB c/u)**, y Gemini realiza una forma de RAG sobre esos archivos; la guía oficial de prompting de Google se basa en el marco **Persona–Tarea–Contexto–Formato (PTCF)**.
- Para principiantes, **un Gem es suficiente**; NotebookLM, Google AI Studio y Vertex AI son escalones más potentes cuando se necesita más volumen de fuentes o despliegue en producción.

---

## Key Findings (datos verificados)

### 1. Qué es un Gem y requisitos
- **Definición oficial** (gemini.google/overview/gems): *"Gems are your custom AI experts for help on any topic... Gems let you save highly detailed prompt instructions for your most repeatable tasks."* Es una versión guardada de Gemini con instrucciones persistentes y, opcionalmente, archivos de conocimiento.
- **Gems predefinidos (premade) vs personalizados (custom):** Google ofrece Gems predefinidos — **Brainstormer, Career guide, Coding partner, Learning coach, Writing editor** (además del lúdico "Chess champ"). Para principiantes se recomienda copiar uno con "Make a copy" y editar las instrucciones prellenadas, porque sirven de plantilla y enseñan cómo se ve una buena instrucción.
- **Requisito de edad:** cuenta personal, **13 años o más** (o la edad aplicable en tu país). Los Gems se **crean, editan y borran SOLO en la app web** (gemini.google.com); se **usan** en web, móvil y el panel lateral de Google Workspace.
- **Gratis vs pago — historial:** Gems se lanzó en **agosto de 2024** como función de pago (Google Workspace Blog: *"Since launching in August, Gems... have been one of the most used Gemini Advanced features"*). El **13 de marzo de 2025**, Google anunció en su blog oficial que la creación de Gems pasó a ser gratuita: *"Gems let you customize Gemini to create your own personal AI expert on any topic, and are starting to roll out for everyone at no cost in the Gemini app."* Los planes de pago dan límites más altos, ventana de contexto de hasta 1–2M tokens y subidas de video/audio más largas.

### 2. Cómo crear un Gem (paso a paso, según las páginas oficiales support.google.com/gemini/answer/15146780 y /15235603)
1. Ir a **gemini.google.com** → abrir la barra lateral → **"Gems" / "Explore Gems"** (abre el **Gem manager**, identificado con un icono de joya/diamante).
2. Hacer click en **"New Gem"** (botón superior derecho). *Precaución: no confundir con "New Chat".*
3. Escribir un **Nombre** descriptivo + las **Instrucciones**. (Puedes escribir una frase y pulsar **"Use Gemini to re-write instructions"** — el icono de **varita mágica** — para que Gemini expanda y estructure las instrucciones por ti.)
4. **(Opcional) En "Knowledge", "Add files"**: subir desde el dispositivo, desde Google Drive, o conectar un notebook de NotebookLM.
5. **Previsualizar** en el panel derecho (escribir un prompt de prueba y pulsar "Submit"). **El preview NO guarda automáticamente.**
6. Hacer click en **"Save"**. El Gem aparece en la barra lateral y se sincroniza a móvil y al panel de Workspace.
- La interfaz es de **pantalla dividida**: columna izquierda de configuración (nombre, instrucciones, conocimiento) y panel derecho de previsualización en tiempo real. Iterar: ajustar instrucciones → probar → repetir. Revisar y refinar los Gems periódicamente.

### 3. Archivos de conocimiento (Knowledge) — límites
- **Hasta 10 archivos por Gem; cada archivo hasta 100 MB** (video hasta 2 GB; los límites de duración de video/audio aumentan con Google AI Pro/Ultra).
- Texto oficial: *"Gemini Apps support most file types."* Los tipos de documento concretos citados públicamente (**fuente secundaria — TechWiser, no página oficial de Google**) son: documentos/texto — **Google Docs, TXT, DOC, DOCX, PDF, RTF, DOT, DOTX, HWP, HWPX**; hojas de cálculo — **Google Sheets, CSV, TSV, XLS, XLSX**.
- **Google Docs/Sheets se sincronizan automáticamente** (Gemini usa la versión más reciente); otros tipos hay que **re-subirlos** al actualizarlos.
- Se puede conectar un **notebook de NotebookLM** como fuente (More uploads → Notebooks).
- Opción **"Disable knowledge citations"** para ocultar las citas a los archivos en las respuestas.
- El almacenamiento de Gemini Apps es **independiente** del de Drive; si se llena, hay que borrar actividad antigua.

### 4. Modelos detrás de Gems (mediados de 2026)
- **Modelo por defecto de la app Gemini: familia Gemini 3.x Flash.** Gemini 3 Flash pasó a ser el default en **diciembre 2025**; **Gemini 3.5 Flash** se lanzó globalmente el **19 de mayo de 2026** (seleccionable en el menú de modelos).
- **Nivel avanzado "Pro": Gemini 3.1 Pro** (lanzado el **19 de febrero de 2026**), con ventana de contexto de **hasta 2M tokens** en Google AI Pro.
- Google **no designa un único modelo "para Gems"**; los Gems corren sobre los modelos disponibles en el selector de la app Gemini.

### 5. Compartir y publicar un Gem
- Desde **septiembre de 2025** se pueden compartir Gems con un **modelo estilo Google Drive**: roles **Visor (Viewer)** o **Editor**; por enlace o a personas específicas; se puede fijar **fecha de expiración** y **transferir la propiedad**.
- **Solo se puede compartir** si el conocimiento son **archivos de dispositivo o de Drive**; otros tipos (carpetas de código, etc.) **deshabilitan** el botón Share (Google Workspace Updates: *"Gems are only shareable when any custom knowledge is either uploaded from a device to the Gem, or files added from Google Drive... Once shared, Gems are stored in Google Drive."*).
- Los Gems compartidos se guardan en una carpeta **"Gemini Gems"** en Drive; un **Visor no ve** los archivos de conocimiento (si hace una copia, los archivos quedan inaccesibles y el Gem da error).

### 6. Planes y precios (2026) — nombres verificados
- **"Gemini Advanced" se renombró a "Google AI Pro"** (marzo 2026); **Google One AI Premium** también pasó a llamarse **Google AI Pro** (mismas funciones, mismo precio; cambia el nombre en la factura).
- **Tres niveles consumidor:** Google AI Plus (~$7.99–$9.99/mes), **Google AI Pro ($19.99/mes)**, Google AI Ultra (precio reportado de $249.99/mes, reducido posteriormente en 2026).
- **Workspace:** Google dejó de vender el add-on independiente de Gemini (Business/Enterprise) en 2025; **Gemini quedó incluido** en los planes Business Standard/Plus y Enterprise.

---

## Details

### Ingeniería de prompts (frameworks)
- **Marco oficial de Google: Persona, Task, Context, Format (PTCF).** De la guía oficial *"Gemini for Workspace Prompting Guide 101"*: las cuatro áreas son **Persona, Tarea, Contexto, Formato**; *"You don't need to use all four, but using a few will help"*; *"Always remember to include a verb or command as part of your task; this is the most important component."* Además, según la misma guía: *"Based on what we have learned during our Workspace Labs program, the most successful prompts average around 21 words, yet prompts people often try... are often short — usually less than nine words."* (Las instrucciones de un Gem se escriben igual que un buen prompt.)
- **RTF (Role, Task, Format):** el más simple y rápido; bueno para tareas cotidianas.
- **RACE (Role, Action, Context, Expectation):** minimalista de cuatro componentes para tareas rápidas; buen punto de partida.
- **RISEN (Role, Instructions, Steps, End goal, Narrowing):** ideal cuando el agente debe seguir un **proceso de varios pasos**; alineado con chain-of-thought; añade más tokens a la salida.
- **CO-STAR (Context, Objective, Style, Tone, Audience, Response):** óptimo para **control de tono, estilo y audiencia** (marketing, copy editorial).
- **CRISPE (Capacity/role, Insight, Statement, Personality, Experiment):** balance entre análisis estructurado y experimentación.
- **CRAFT / RTCCO (Role, Task, Context, Constraints, Output):** variantes para prompts estructurados y modulares.
- **Conclusión:** no hay un framework "mejor"; se elige según la tarea. Para principiantes y para Gems, **PTCF de Google** es el punto de partida natural; se puede escalar a RISEN/CO-STAR según la complejidad.

### Estructura recomendada de un system prompt para un agente
Bloques en orden (aprovechando primacía al inicio y recencia al final):
1. **Identidad/Rol** (1–3 frases: quién es el agente y su propósito).
2. **Objetivo/Alcance** (qué hace y qué **NO** hace; límites).
3. **Funciones/Flujo de trabajo** (patrón: clarificar → planear → actuar → verificar).
4. **Estilo de comunicación** (tono, longitud, idioma del usuario).
5. **Restricciones/Reglas** (usar lenguaje fuerte tipo **NEVER/MUST** para reglas duras; "prefer/recommended" para reglas blandas).
6. **Formato de salida** (estructura, listas, secciones, esquema).
7. **Recordatorios al final** (reforzar las reglas críticas).

**Buenas prácticas (de guías de diseño de agentes 2026):** estructurar con encabezados Markdown; escribir **instrucciones positivas** ("Haz X" mejor que "No hagas Y"); no inflar con superlativos ni "lore" innecesario; colocar la identidad al inicio y las reglas no negociables al final (para evitar el problema *"lost in the middle"* — en pruebas de producción mover una regla del medio al final subió la precisión del 78% al 96%); incluir **2–3 ejemplos few-shot**. En algunas plataformas el system prompt tiene límite (~9,000 caracteres): no meter manuales completos en el prompt, sino en la **base de conocimiento**, e instruir al agente a consultarla.

### Técnicas de prompting
- **Few-shot:** dar 1–3 ejemplos del resultado deseado.
- **Chain-of-thought (CoT):** pedir razonamiento paso a paso ("piensa en voz alta"); reduce el *"coherent nonsense"*/alucinaciones; útil para tareas complejas.
- **Delimitadores:** separar instrucciones del contexto/datos con etiquetas (p. ej. `<context>...</context>`) o secciones Markdown.
- **Temperatura:** controla la aleatoriedad/creatividad. **0 = más determinista** (siempre el token más probable); valores altos = más aleatorio/creativo. Para tareas factuales/RAG, usar **temperatura baja**. *(En Gems no se expone control de temperatura; el comportamiento se controla solo vía instrucciones.)*
- **Anti-alucinación:** instruir explícitamente a no inventar; pedir que cite fuentes; decir "no sé" cuando falte la información.

### RAG (Retrieval-Augmented Generation) explicado para principiantes
- **Qué es:** técnica que permite a un LLM "buscar" en una base de conocimiento **antes** de responder, para **fundamentar (ground)** la respuesta en información real, actual o privada. Analogía: en vez de memorizar todas las calles de una ciudad (fine-tuning, que queda desactualizado), usa un **GPS** que consulta el mapa actual cada vez (RAG).
- **Por qué se usa:** reduce alucinaciones, aporta conocimiento actualizado/privado, y es **más barato que reentrenar** el modelo.
- **Cómo funciona (pipeline):** **Ingestión** (cargar documentos) → **Chunking** (fragmentar) → **Embeddings** (convertir cada fragmento en un vector numérico que captura su significado) → **Vector store** (base de datos vectorial) → **Recuperación** (la pregunta se convierte en vector y se buscan los fragmentos más similares, p. ej. por **similitud coseno**) → **Aumento** (se inyectan los fragmentos recuperados en el prompt) → **Generación** (el LLM responde usando ese contexto).
- **Relación con Gems:** cuando subes archivos de conocimiento a un Gem, **Gemini hace una forma de RAG** sobre ellos (recupera lo relevante y lo cita). NotebookLM funciona igual: *"NotebookLM answers questions based on the information provided in your uploaded sources. If the answer isn't in the source material, it won't provide a response."*

### Buenas prácticas para preparar documentos a "embeber"
- **Chunking:** fragmentos autocontenidos. Tamaño recomendado **256–512 tokens** para preguntas factuales, **1024+** para preguntas analíticas; punto medio práctico **400–512 tokens**; **solapamiento (overlap) 10–20%** (50–100 tokens en un chunk de 500) para no perder contexto en los bordes. *(Matiz: un análisis sistemático de enero 2026 con SPLADE/Mistral encontró que el overlap no aportó beneficio medible y solo aumentó el costo de indexación — conviene probar en cada caso.)*
- **Estructura clara:** usar **encabezados** (Markdown/títulos). La estrategia de chunking "by title" preserva los límites de sección para que **un chunk no mezcle dos temas**; conviene convertir PDFs a Markdown limpio antes de fragmentar.
- **Chunks autocontenidos / contextual retrieval:** anteponer a cada chunk un breve contexto (título / ruta de encabezado / resumen). **Anthropic** reporta (sept. 2024) que su *"Contextual Retrieval"* **reduce los fallos de recuperación un 49%** (tasa de fallo top-20 de 5.7% → 2.9%) y **67% combinado con un re-ranker** (→ 1.9%).
- **Evitar ambigüedad:** resolver referencias (pronombres como "esto", "él"); idealmente **una idea/hecho por fragmento** (técnica de "proposiciones"); añadir metadatos/etiquetas.
- **Para un Gem** (que hace el chunking por ti, sin que controles los parámetros): estructurar el documento con encabezados claros, **secciones cortas y autocontenidas**, un glosario y lenguaje sin ambigüedad ayuda directamente a la calidad de la recuperación.

### Prompting anti-alucinación para un agente RAG (responder solo desde los documentos)
Patrones verificados en la práctica de la industria:
- **"Answer ONLY based on the provided context"** debe ser la **primera instrucción**, ubicada en el **system prompt** (no en el mensaje de usuario) y **antes** del bloque de contexto.
- *"If the answer is not clearly present in the documents, say: 'I don't have enough information in the available documents to answer this.' Do not use knowledge from outside the provided documents."* — la cláusula "do not use outside knowledge" es la que evita que el modelo rellene huecos con su entrenamiento.
- Especificar el **formato exacto de citas**; añadir: *"Do not make claims you cannot cite to a specific document."*
- **Orden recomendado:** system prompt (grounding + reglas de citas + qué hacer si falta info) → bloque de contexto (chunk más relevante primero) → pregunta del usuario al final.
- **Balance:** si es **demasiado** restrictivo, el agente dirá "no sé" incluso cuando la respuesta sí está; hay que dejar claro que **evalúe si la evidencia existe** antes de rechazar.

### Otras plataformas del ecosistema Google (cuándo usar cada una)
- **NotebookLM:** asistente de investigación fundamentado en **TUS** fuentes. Gratis (confirmado por NotebookLM Help oficial): **100 notebooks, 50 fuentes/notebook, 500,000 palabras o 200 MB por fuente**; soporta PDFs, Docs, Slides, texto, URLs, YouTube y audio. Planes: Plus 100 fuentes, Pro 300, Ultra 600. Ahora corre sobre **Gemini 3** y puede conectarse a la app Gemini. **Mejor que subir un solo PDF a un Gem cuando hay muchas fuentes**: se puede curar un notebook y conectarlo como conocimiento del Gem.
- **Google AI Studio:** sandbox **gratuito** en el navegador para probar prompts y la API de Gemini; ideal para prototipar; solo requiere cuenta Google; exporta código. Para experimentar y validar ideas rápido.
- **Vertex AI / Vertex AI Agent Builder** (parte de la **"Gemini Enterprise Agent Platform"** rebautizada en Cloud Next 2026): plataforma **empresarial** para construir, desplegar y **gobernar** agentes en producción (ADK, Agent Studio, Agent Garden, Model Garden con 200+ modelos, Agent Engine, memoria persistente). Para sistemas multi-agente complejos; **curva de aprendizaje y costo altos**; pago por uso (nuevos usuarios: $300 en créditos).
- **Gemini API:** acceso por token a los modelos para desarrolladores. Nota: el **fine-tuning ya no está disponible en la Gemini API ni en AI Studio** (con la deprecación de Gemini 1.5 Flash-001 en mayo de 2025; sí se soporta en Gemini Enterprise Agent Platform). La personalización para la mayoría se hace vía **prompt engineering, RAG y Gems**.
- **Cuándo basta un Gem:** tareas repetibles personales o de equipo, hasta 10 archivos, sin programar. **Cuándo escalar:** muchas fuentes → **NotebookLM**; prototipo de app/API → **AI Studio**; producción, gobernanza, conectores a CRM/ERP → **Vertex AI**.

### Conceptos fundamentales (glosario para principiantes)
- **LLM (Large Language Model):** modelo que **predice el siguiente "token"** según patrones aprendidos; no "consulta" hechos en una base de datos.
- **Agente de IA vs chatbot:** un **chatbot** procesa una consulta y responde (sin memoria entre turnos, sin herramientas); un **agente** es multi-paso, persistente y **usa herramientas** (lee/escribe archivos, ejecuta código, busca en la web, llama a sub-agentes). *"The distinction between a chatbot and an AI agent is architectural, not merely rhetorical."*
- **Token:** fragmento de palabra (≈ 4 caracteres ≈ 0.75 palabras en inglés).
- **Ventana de contexto (context window):** máximo de tokens que el modelo "lee" a la vez (su "escritorio de trabajo"); incluye system prompt + historial + documentos + salida. Gemini 3.1 Pro llega a **2M tokens**. Al llenarse, lo más antiguo se trunca → más riesgo de alucinaciones.
- **Temperatura:** la "creatividad"/aleatoriedad del modelo (0 = determinista).
- **Alucinación:** salida segura y bien escrita pero **factualmente incorrecta**; es una consecuencia de cómo funcionan los LLMs (predicen lo probable, no lo verdadero).
- **Embedding:** representación numérica (vector) del significado de un texto.
- **Chunking:** dividir documentos en fragmentos para indexarlos y recuperarlos.
- **Grounding (fundamentación):** anclar las respuestas en fuentes reales.

### Meta-prompting y el "agente que crea agentes"
- El propio Gemini incluye el botón **"Use Gemini to re-write instructions"** (varita mágica) que reescribe y expande instrucciones — es **meta-prompting integrado** y, según el product lead de Gems, ayuda a los usuarios a "escribir como un prompt engineer".
- **Patrón recomendado para el agente "creador de agentes"** (estilo "Westy"): que (1) haga **preguntas de clarificación** al usuario principiante, (2) genere un **borrador de instrucciones estructuradas** (PTCF + los 7 bloques del system prompt), (3) recomiende qué **archivos de conocimiento** subir y cómo estructurarlos, y (4) explique cómo **probar e iterar**. Truco práctico para enseñar a usuarios: *"I want to create a Gem that helps me with [tarea]. Ask me 5 questions to clarify what this Gem should do... Then write comprehensive instructions I can paste into a new Gem."*

---

## Recommendations

1. **Para el documento de conocimiento RAG (bilingüe ES/EN):** estructurar con **encabezados claros y secciones cortas autocontenidas** (una idea por sección), incluir un **glosario bilingüe**, **definir cada término la primera vez** que aparece, y mantener cada concepto independiente para que el chunking de Gemini recupere bien. Incluir los **pasos numerados** de creación y los **límites concretos** (10 archivos, 100 MB, modelos 2026, planes con nombres actuales). Para versión bilingüe, considerar separar bloques ES y EN bajo encabezados distintos (p. ej. "ES —" / "EN —") para que un chunk no mezcle idiomas.

2. **Para el prompt de sistema del agente "creador de agentes":** usar la **estructura de 7 bloques** (Identidad → Alcance → Flujo → Estilo → Restricciones → Formato → Recordatorios); instruir **grounding estricto** ("responde solo con base en tu base de conocimiento; si no está, dilo claramente"); incluir un **flujo de preguntas de clarificación** para principiantes; salida en el **idioma del usuario** (ES/EN); e incluir **2–3 ejemplos few-shot** de cómo guiar paso a paso a un novato a crear su primer Gem.

3. **Verificar al publicar:** nombres de producto actuales (**Google AI Pro**, no "Gemini Advanced"), modelos (**Gemini 3.x Flash / 3.1 Pro**), y que **la creación de Gems es gratuita**.

4. **Umbrales para escalar (incluir como guía en el agente):** si el usuario necesita **>10 archivos** o **>50 fuentes**, dirigir a **NotebookLM**; si necesita una **app o API**, a **Google AI Studio**; si necesita **producción/gobernanza/conectores empresariales**, a **Vertex AI**.

---

## Caveats
- **Volatilidad:** los nombres de productos, modelos y precios de Google cambian con frecuencia; verificar en fuentes oficiales antes de publicar. Algunos precios (Ultra) variaron a lo largo de 2026.
- **Lista de extensiones de archivo:** la enumeración concreta de tipos soportados por Gems proviene de **prensa secundaria (TechWiser), no de una página oficial** de Google; Google solo dice *"most file types"*. Verificar en support.google.com/gemini/answer/14903178.
- **RAG en Gems es una caja parcialmente cerrada:** Gemini "hace una forma de RAG" sobre los archivos de un Gem, pero Google **no documenta públicamente** los detalles (chunking, embeddings). Las buenas prácticas de chunking citadas aplican principalmente a **pipelines propios** (Vertex AI, etc.), no necesariamente al motor interno de Gems; aun así, **documentos bien estructurados mejoran la recuperación en cualquier sistema**.
- **Los Gems pueden alucinar** aun con archivos de conocimiento; siempre verificar las salidas críticas (datos, cálculos, temas legales/médicos).
- **Fuentes oficiales clave para citar en el documento final:**
  - Crear/usar Gems: support.google.com/gemini/answer/15146780 y support.google.com/gemini/answer/15235603
  - Archivos y límites: support.google.com/gemini/answer/14903178
  - Compartir Gems: support.google.com/gemini/answer/16504957 y workspaceupdates.googleblog.com
  - Overview de Gems: gemini.google/overview/gems
  - Modelos y release notes: gemini.google/release-notes y ai.google.dev/gemini-api/docs/models
  - Planes: one.google.com/about/google-ai-plans y gemini.google/subscriptions
  - Guía de prompting (PDF oficial): services.google.com/fh/files/misc/gemini_for_workspace_prompt_guide_october_2024_digital_final.pdf
  - NotebookLM: support.google.com/notebooklm/answer/16269187 y /16215270
  - RAG (Google Cloud): cloud.google.com/use-cases/retrieval-augmented-generation
  - Contextual Retrieval (Anthropic): anthropic.com/news/contextual-retrieval