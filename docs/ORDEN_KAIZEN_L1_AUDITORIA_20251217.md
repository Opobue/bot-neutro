# ORDEN_KAIZEN_L1_AUDITORIA_20251217 – Auditoría global y sincronización contratos-código

## Resumen ejecutivo
- Alcance L1 (gobernanza): solo documentación y verificación; no se tocan flujos funcionales.
- Se auditaron el backend `bot-neutro` y el cliente `clients/munay-dashboard` contra los contratos vigentes.
- Hallazgos clave: en el momento de la auditoría el README afirmaba que `/audio` estaba stub y respondía 501, pero el código actual define un pipeline completo; se marca el README como desfasado y se corrige en `HISTORIAL_PR` (“Correcciones menores tras auditoría L1”). El rate limit se aplica solo a `/audio` con API key presente. El storage de sesiones es exclusivamente en memoria y sin políticas de retención/listado. El cliente oficial cumple el flujo básico pero depende de códigos 400/401 y no del 422 esperado en contrato.
- Evidencia: `README.md` indicaba stub 501; `src/bot_neutro/api.py` implementa `post_audio` con `AudioPipeline.process` y mapeos de error; `tests/test_api_audio.py` cubre rutas de éxito/error y pipeline; `clients/munay-dashboard/src/api/client.ts` consume `/audio` con headers/tier.

## Mapa de carpetas y responsabilidades
- `src/bot_neutro/`: API FastAPI (`/audio`, healthz/readyz/version/metrics), pipeline de audio y almacenamiento en memoria.
- `src/bot_neutro/middleware/`: middlewares de observabilidad y protección (correlación, logging JSON, rate limit, latencia).
- `src/bot_neutro/providers/`: interfaces y providers enchufables (stub por defecto, Azure opt-in para STT/TTS, OpenAI LLM opt-in con fallback a stub).
- `docs/`: contratos y runbooks; incluye contratos de audio, storage, rate limit y cliente oficial.
- `clients/munay-dashboard/`: dashboard React/Vite oficial para `/audio`, con configuración por variables `VITE_*` y componentes de upload/resultados.
- `tests/`: validan contrato `/audio`, storage in-memory y comportamiento de middlewares.

## Inventario de middlewares, providers y endpoints
### Middlewares (FastAPI)
- `RequestLatencyMiddleware`: mide latencia por ruta y alimenta histogramas en memoria.
- `CorrelationIdMiddleware`: asegura header `X-Correlation-Id` en request/response y lo deja en `request.state`.
- `RateLimitMiddleware`: controla `/audio` cuando `RATE_LIMIT_ENABLED=1`, con ventana configurable y allowlist (`/metrics`, `/healthz`, `/readyz`, `/version`).
- `JSONLoggingMiddleware`: emite logs estructurados por petición (método, path, status, corr_id).

### Providers y factory
- STT: `StubSTTProvider` (default); `AzureSTTProvider` opt-in con fallback al stub y fail-fast si faltan credenciales.
- TTS: `StubTTSProvider` (default); `AzureTTSProvider` opt-in con fallback al stub.
- LLM: `StubLLMProvider` (default); `OpenAILLMProvider` opt-in, selecciona modelo por tier (`freemium`/`premium`) y hace fallback a stub en errores.
- Factory selecciona providers por ENV (`AUDIO_STT_PROVIDER`, `AUDIO_TTS_PROVIDER`, `LLM_PROVIDER`).

### Endpoints activos
- `GET /healthz`, `/readyz`, `/version`: respuestas JSON simples con `X-Outcome` preset.
- `GET /metrics`: expone métricas Prometheus (latencia por ruta, rate-limit hits, lecturas/escrituras de memoria, requests/errors totales).
- `POST /audio`: al momento de la auditoría, README declaraba que estaba stub (501), pero el código en `src/bot_neutro/api.py` implementa un pipeline completo (multipart con archivo de audio y metadatos/headers de cliente). Se marca este desfase como hallazgo L1 y se corrige en este PR. Evidencia: `README.md` (sección API) vs. `src/bot_neutro/api.py::post_audio` y pruebas `tests/test_api_audio.py`.

## Flujo `/audio` según código
1. Middleware de correlación y rate limit (si habilitado) se ejecutan antes del handler.
2. Validaciones HTTP iniciales: se rechaza `x-munay-context` inválido y audio vacío; se genera `corr_id` cuando no viene en el request.
3. `AudioPipeline.process` opera sobre el multipart (audio + metadatos) y devuelve `AudioResponseContext` con usage y providers; el código define mapeos de errores a HTTP 4xx/5xx.
4. Al momento de la auditoría el README indicaba stub 501; la presencia de la implementación en `src/bot_neutro/api.py` y tests de `/audio` sugiere que el README estaba desfasado (ya corregido en este PR). Evidencia: `src/bot_neutro/api.py` usa `AudioPipeline.process`; `tests/test_api_audio.py` cubre respuestas 200/400/401/429; `README.md` exponía stub 501.

## Cuadro “Contrato ↔ Código” (estado al 2025-12-17)
| Contrato | Estado | Delta observado |
| --- | --- | --- |
| `CONTRATO_NEUTRO_AUDIO_PIPELINE.md` | **DESFASADO parcial** | Código usa `LLM_PROVIDER` en lugar de `AUDIO_LLM_PROVIDER`; no hay caso `storage_error` en pipeline; validaciones extra de `x-munay-context` no están descritas; al momento de la auditoría el README declaraba stub 501 mientras el código implementa pipeline (corregido en `HISTORIAL_PR`). Evidencia: `src/bot_neutro/providers/factory.py` selecciona `LLM_PROVIDER`; `src/bot_neutro/audio_pipeline.py` no define `storage_error`; validación de `x-munay-context` en `src/bot_neutro/api.py`; README declaraba stub. |
| `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md` | **DESFASADO** | Implementación solo in-memory sin índices ni persistencia; `request_duration_seconds` siempre `None`; no hay políticas de retención ni control de lectura por usuario/API key antes de exponer endpoints. Evidencia: `src/bot_neutro/audio_storage_inmemory.py` guarda en memoria y deja `request_duration_seconds=None`. |
| `CONTRATO_NEUTRO_RATE_LIMIT.md` | **DESFASADO** | Rate limit solo se aplica a `/audio` y solo cuando hay `X-API-Key`; contrato menciona más rutas. No hay logging específico de rate limit, aunque sí métrica `sensei_rate_limit_hits_total` y headers esperados. Evidencia: `src/bot_neutro/middleware/rate_limit.py` filtra por path `/audio` y requiere API key; la misma implementación expone headers/métrica. |
| `CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md` | **OK con nota** | Dashboard permite seleccionar tier, envía `X-API-Key` y renderiza transcript/reply/usage/provider_llm/corr_id. Maneja errores 401 y 400; las validaciones 422 son internas de la UI y no del backend (el backend devuelve 400 para audio faltante). Evidencia: `clients/munay-dashboard/src/api/client.ts` y `clients/munay-dashboard/src/components/AudioUploader.tsx` manejan tier y headers; backend `tests/test_api_audio.py::test_audio_missing_file` retorna 400. |
| `CLIENTE_OFICIAL_MUNAY_TECNICO_V1.md` | **OK** | La estructura, variables `VITE_*` y comandos documentados coinciden con el código del dashboard (config, api/client.ts, componentes). Evidencia: `clients/munay-dashboard/vite.config.ts`, `.env.example` y estructura de `src/` alinean con el contrato. |
| `UX_CLIENTE_OFICIAL_MUNAY_V1.md` | **OK con nota** | La UI muestra upload, selector de tier, resultados y badge “Modo stub activo”; no incluye opción de grabar audio (permitido como iteración futura). Evidencia: componentes `clients/munay-dashboard/src/components/AudioUploader.tsx`/`clients/munay-dashboard/src/components/ResultPanel.tsx` muestran upload y tier, sin control de grabación. |

## Privacidad y seguridad (hallazgos)
- El storage es in-memory sin autenticación ni autorización; cualquier endpoint futuro de lectura deberá definir quién puede listar por `user_external_id` o `api_key_id` y cómo anonimizar datos.
- No existen políticas de retención, eliminación ni anonimización de sesiones; los objetos permanecen en memoria hasta reinicio.
- Los providers opt-in (Azure/OpenAI) dependen de credenciales en entorno; no hay auditoría ni cifrado en repositorio.

## Zonas oscuras / TODOs identificados
- Control de lectura de sesiones: falta contrato de quién puede acceder a `list_by_user`/`list_by_api_key` y cómo exponer endpoints seguros.
- Retención y límites de almacenamiento: no hay expiración ni métricas de tamaño de storage in-memory.
- LLM tiers y costos: no existe política por API key para `freemium`/`premium`; el backend acepta el header pero no valida planes ni cuotas.
- Rate limit: cobertura solo para `/audio`; faltan logs estructurados de rechazos y definición para otras rutas futuras.
- Observabilidad: `/metrics` no expone histograma por provider ni latencias separadas por etapa; solo per-route.

Recomendación: emitir órdenes futuras para mantener README y contratos alineados de forma continua, definir la política de sesiones (retención, lectura segura) y formalizar la política de tiers/planes por API key, incluyendo la resolución definitiva entre 400/422 para validaciones.

## Notas sobre pruebas ejecutadas
- Este documento no afirma ejecución de tests; el estado de tests/cobertura se verifica por CI (`.github/workflows/ci_tests.yml`).

## Evidencias consultadas
- Contratos: `CONTRATO_NEUTRO_AUDIO_PIPELINE.md`, `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`, `CONTRATO_NEUTRO_RATE_LIMIT.md`, `CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md`, `CLIENTE_OFICIAL_MUNAY_TECNICO_V1.md`, `UX_CLIENTE_OFICIAL_MUNAY_V1.md`.
- Repositorio: `README.md`, `docs/HISTORIAL_PR.md`, `src/bot_neutro/api.py`, `src/bot_neutro/audio_pipeline.py`, `src/bot_neutro/middleware/`, `src/bot_neutro/providers/`, `clients/munay-dashboard/` (estructura y componentes principales), `tests/` (cobertura de `/audio` y métricas).
