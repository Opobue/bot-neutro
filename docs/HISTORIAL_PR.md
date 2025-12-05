# HISTORIAL_PR – Bot Neutro / Munay

> Convención: el último cambio va arriba. Solo registramos cambios que
> afectan contratos, comportamiento observable o el Norte del proyecto.

## 2025-12-05 – Gobernanza SKB formal + CI de tests/cobertura

- Se crea el workflow `.github/workflows/ci_tests.yml` que ejecuta `pytest -q` y `pytest --cov=src --cov-fail-under=80` en push/PR a `main`.
- Se establece infraestructura de ADRs en `docs/adr/` con `ADR_TEMPLATE.md` como plantilla obligatoria.
- Se agrega `docs/CONTRATO_SKB_GOBERNANZA.md` para formalizar D→D→C, bloqueos, contracts-first y reglas de pruebas/cobertura.
- Se agrega `docs/CONTRATO_NEUTRO_CONTRIBUCION.md` como checklist previo a PR.
- Se refuerza que el CI debe validar cobertura ≥80% para aprobar PRs y que la gobernanza SKB pasa a ser contrato formal del repositorio.

## 2025-12-04 – Estandarización de cobertura con pytest-cov

- Se define `pytest --cov=src --cov-fail-under=80` como comando estándar de
  cobertura para el proyecto, asegurando un umbral mínimo de 80% de cobertura.
- Se añade `pytest-cov` a las dependencias de desarrollo (pyproject/requirements)
  para que cualquier entorno pueda ejecutar el comando de cobertura sin errores.
- Este cambio no modifica contratos ni código de runtime; formaliza la práctica
  de calidad ya aplicada localmente (17 tests en verde y ~98% de cobertura).

## 2025-12-04 – Ajuste de semántica X-Outcome para /audio

- Se actualiza `CONTRATO_NEUTRO_AUDIO_PIPELINE.md` para alinear la semántica de
  headers con la implementación actual del endpoint `/audio`:
  - Respuestas exitosas usan `X-Outcome: success` y
    `X-Outcome-Detail: audio_processed`.
  - Las respuestas de error (`4xx`/`5xx`) mantienen `X-Outcome: error` y uno de
    los códigos `audio.*` / `auth.*` definidos en la tabla de errores.
- No se realizan cambios en código; este ajuste solo sincroniza la
  documentación del contrato con el comportamiento ya cubierto por los tests
  del endpoint `/audio`.

## 2025-12-04 – Alineación contrato AudioResponseContext con implementación

- Se actualiza `CONTRATO_NEUTRO_AUDIO_PIPELINE.md` para que `AudioResponseContext`
  use `tts_url` como campo canónico de URL TTS (en lugar de `audio_url` /
  `tts_audio_url`) y documentar los campos actualmente devueltos por el stub:
  `session_id`, `corr_id`, `tts_url`, `usage.input_seconds`, `usage.output_seconds`,
  `meta`.
- Se actualiza `MUNAY_CONTRATO_MODULO_AUDIO.md` para que el contrato del módulo
  de audio en Munay consuma `tts_url` y conozca `session_id`, `corr_id` y
  `meta.context`.
- No se modifican firmas de código; este cambio sincroniza documentación con el
  comportamiento ya implementado en el endpoint `/audio`.

## 2025-12-02 – Definición del NORTE MUNAY v2.1 + validación automática

- Se crea `docs/02_ESTADO_Y_NORTE.md` como documento fuente del NORTE MUNAY v2.1:
  - Establece principios operativos.
  - Define el modelo contracts-first (contratos → historial PR → ADR → código).
  - Fija SLOs oficiales de audio, reglas de observabilidad y flujo Kaizen (L1/L2/L3).
  - Define el protocolo de inicio para nuevos hilos (repositorio como fuente de verdad).
- Se crea el workflow `validate_norte.yml` para:
  - Verificar la existencia y encabezados de:
    - `docs/02_ESTADO_Y_NORTE.md`
    - `docs/HISTORIAL_PR.md`
  - Fallar el CI cuando haya cambios en:
    - Contratos NEUTRO (`docs/CONTRATO_*`)
    - Contratos MUNAY (`docs/MUNAY_*`)
    - El propio NORTE (`docs/02_ESTADO_Y_NORTE.md`)
    que no estén acompañados por una actualización de `docs/HISTORIAL_PR.md`.
- Este cambio consolida el NORTE como contrato de gobernanza y hace obligatorio
  mantener el historial PR sincronizado con cualquier cambio de contrato o del NORTE.

## 2025-12-02 – Rate limit en /audio + métricas dinámicas

- Se implementa rate limit real sobre `/audio`, controlado por variables de entorno:
  - `RATE_LIMIT_ENABLED`
  - `RATE_LIMIT_AUDIO_WINDOW_SECONDS`
  - `RATE_LIMIT_AUDIO_MAX_REQUESTS`
- Solo se limita `/audio`; rutas `/healthz`, `/readyz`, `/version` y `/metrics` quedan en allowlist.
- Las respuestas 429 devuelven:
  - `{"detail": "rate limit exceeded"}`
  - Headers: `X-Outcome: error`, `X-Outcome-Detail: rate_limit`, `Retry-After`.
- Se añade `InMemoryMetrics` (`metrics_runtime.py`) para registrar:
  - `sensei_requests_total{route="…"}`
  - `errors_total{route="…"}`
  y exponerlos dinámicamente en `/metrics`, manteniendo el payload estático original.
- Contratos relacionados:
  - `CONTRATO_NEUTRO_RATE_LIMIT.md`
  - `CONTRATO_NEUTRO_OBSERVABILIDAD.md`

## 2025-12-02 – Pipeline de audio + storage de sesiones + headers Munay

- Se define el contrato lógico del pipeline de audio:
  - `CONTRATO_NEUTRO_AUDIO_PIPELINE.md`:
    - `AudioRequestContext`, `UsageMetrics`, `AudioResponseContext`, `PipelineError`.
    - Interfaz `AudioPipeline.process(ctx)`.
- Se implementa `StubAudioPipeline` en `audio_pipeline_stub.py`:
  - Valida `api_key`, tipo MIME y que el audio no esté vacío.
  - Genera respuesta stub con `transcript`, `reply_text`, `usage` y `session_id`.
- Se añade storage en memoria de sesiones de audio:
  - `audio_storage_inmemory.py` con `AudioSession` e `InMemoryAudioSessionRepository`.
  - `DEFAULT_AUDIO_SESSION_REPOSITORY` compartido.
  - Contrato documentado en `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`.
- El endpoint `/audio` ahora:
  - Acepta `multipart/form-data` con campo `file`.
  - Usa `X-API-Key` y `X-Correlation-Id`.
  - Acepta headers cliente Munay:
    - `x-munay-user-id`
    - `x-munay-context` (valores válidos: `diario_emocional`, `coach_habitos`, `reflexion_general`).
  - Rechaza contextos inválidos con 400 y `X-Outcome-Detail: audio.bad_request`.
  - Propaga `munay_user_id` y `munay_context` como metadatos hacia la sesión de audio:
    - `user_external_id`
    - `meta_tags["context"]`
- Se añaden tests de contrato de `/audio`:
  - `tests/test_audio_contract.py` cubre:
    - Happy path.
    - Errores por MIME inválido, audio vacío, falta de API key.
    - Persistencia en `DEFAULT_AUDIO_SESSION_REPOSITORY`.
    - Enriquecimiento con headers Munay.
- Contratos relacionados:
  - `CONTRATO_NEUTRO_AUDIO.md`
  - `CONTRATO_NEUTRO_AUDIO_PIPELINE.md`
  - `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`
  - `MUNAY_CONTRATO_MODULO_AUDIO.md`
  - `MUNAY_CONTRATO_PROGRESO_USUARIO.md`

## 2025-12-02 – Ajuste contratos de headers y observabilidad

- Se aclara la semántica de headers estándar en `CONTRATO_NEUTRO_HEADERS.md`:
  - `X-Outcome` es obligatorio en todas las respuestas:
    - `ok` para 2xx
    - `error` para 4xx/5xx
  - `X-Outcome-Detail` se reserva para errores (`X-Outcome=error`).
- Se garantiza que `/healthz`, `/readyz`, `/version` y `/metrics`:
  - Siempre incluyen `X-Outcome`.
  - Se integran con las métricas dinámicas a través de `METRICS.inc_request(route)`.
- Se mantiene el payload estático de `/metrics` para compatibilidad con tests previos,
  añadiendo solo líneas dinámicas para contadores por ruta.

