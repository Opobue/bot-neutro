# HISTORIAL_PR – Bot Neutro / Munay

> Convención: el último cambio va arriba. Solo registramos cambios que
> afectan contratos, comportamiento observable o el Norte del proyecto.

## 2026-01-02 – Corrección de análisis estático y pruebas de preservación de constantes

- Se agregan pruebas de regresión para blindar constantes globales de contrato:
  - `STATS_MAX_SESSIONS` en `src/bot_neutro/api.py`.
  - `TIER_FREEMIUM`, `TIER_PREMIUM`, `TIERS`, `TIER_ORDER` en `src/bot_neutro/llm_tiers.py`.
  - `METRICS` en `src/bot_neutro/metrics_runtime.py`.
- Se valida el cumplimiento de análisis estático y cobertura conforme a los contratos habilitantes.
- Contratos habilitantes citados:
  - `CONTRATO_INFRAESTRUCTURA_GITHUB.md` (Ruff, Mypy y Pytest en CI).
  - `CONTRATO_NEUTRO_CONTRIBUCION.md` (pytest y cobertura ≥80 %).
  - `CONTRATO_SKB_GOBERNANZA.md` (protocolo D→D→C).
  - `NORTE v2.1` (SLOs y UI como contrato).

## 2025-12-30 – Blindaje de Vanguardia: Implementación de Ruff, Mypy y Contrato de Infraestructura de GitHub.

- 2025-12-30 – Blindaje de Vanguardia: Implementación de Ruff, Mypy y Contrato de Infraestructura de GitHub.

## 2025-12-28 – Hardening de API: Errores 500, CORS configurable y optimización de CI

- FIX: Restauración de la constante STATS_MAX_SESSIONS eliminada accidentalmente durante el hardening de CORS.
- FIX: Sincronización de nombres de Jobs en CI para resolver bloqueo de Branch Protection.
- Se implementó un manejador global de excepciones en `api.py` para asegurar que los errores 500 devuelvan JSON con headers de contrato (`X-Outcome`, `X-Correlation-Id`).
- Se hizo configurable la lista de orígenes CORS mediante la variable de entorno `MUNAY_CORS_ORIGINS`.
- Se optimizó el workflow de CI (`ci_tests.yml`) eliminando la ejecución redundante de pytest.
- Se añadieron tests de regresión (`tests/test_api_hardening.py`) para validar el comportamiento de los headers en errores 500 y la configuración de CORS.

## 2025-12-24 – CI/Workflows habilitados para develop

- Se actualizaron los triggers de workflows guardianes para incluir `develop` junto a `main`.
- Archivos: `.github/workflows/ci_tests.yml`, `.github/workflows/validate_norte.yml`.
- Resultado CI: pendiente de ejecución en GitHub (local no ejecutado).

## 2025-12-23 – Persistencia y retención L2 de sesiones `/audio`

- Se reemplaza el storage in-memory por un repositorio persistente en disco con TTL y purga automática configurable.
- Se incorporan flags para persistir `transcript`/`reply_text` con TTL máximo de 1 día y sanitización de `client_meta` sin PII.
- Se amplían tests de retención, purga y métricas, y se actualiza el NORTE/ENV_VARS para reflejar la persistencia y el bloqueo de endpoints de lectura.

## 2025-12-22 – Contrato Storage & Retención de Sesiones (contracts-first)

- Se crea `CONTRATO_NEUTRO_SESIONES_STORAGE_V1.md` definiendo modelo de datos, retención/TTL, control de acceso y observabilidad declarativa para sesiones de audio.
- Se actualiza `02_ESTADO_Y_NORTE.md` para reflejar el contrato y mantener el bloqueo de persistencia/lecturas hasta L2.
- Sin cambios runtime.

## 2025-12-22 – Implementación L2 enforcement tiers LLM en /audio

- Se valida el header `x-munay-llm-tier` contra el tier autorizado por API key (`freemium|premium`), rechazando valores inválidos con `400` (`X-Outcome-Detail=llm.tier_invalid`).
- Se bloquean escaladas de tier con `403` (`X-Outcome-Detail=llm.tier_forbidden`), incrementando `llm_tier_denied_total{route="/audio",requested_tier,authorized_tier}` y `errors_total{route="/audio"}` y emitiendo logs estructurados (logger `extra`) con `requested_tier`, `authorized_tier`, `api_key_id`, `corr_id`.
- Se actualizan tests de enforcement y métricas, y se documenta el estado en el NORTE.

## 2024-12-19 – Hardening api_key_id derivado end-to-end

- Se deriva `api_key_id` con SHA-256 truncado en `/audio` y `/audio/stats`, sin persistir secretos ni aceptar `X-API-Key-Id` de cliente.
- `/audio/stats` filtra por el `api_key_id` derivado y mantiene respuesta agregada sin PII.
- Rate limit usa el `api_key_id` derivado como clave interna.

## 2025-12-17 – Política de tiers/costos LLM por API-Key (contracts-first, docs-only)

- Se crea `CONTRATO_NEUTRO_LLM_TIERS_COSTOS_V1.md` para definir los tiers permitidos (`freemium|premium`), las cuotas parametrizables y la regla de que la API-Key es la única fuente de verdad; el header `x-munay-llm-tier` es solo `tier_solicitado`.
- Se actualiza `02_ESTADO_Y_NORTE.md` para referenciar el nuevo contrato y dejar explícito que el enforcement llegará en L2 (este PR no cambia runtime; solo define la política contractual): `/audio` debe rechazar escaladas de tier, devolver `X-Outcome-Detail=llm.tier_forbidden|llm.tier_invalid` y exponer métricas/logs de denegación.
- Garantías: (a) bloque de no-escalado por header documentado, (b) semántica de errores/headers/correlación (`X-Outcome`, `X-Outcome-Detail`, `X-Correlation-Id`), (c) observabilidad esperada con `llm_tier_denied_total` e incrementos agregados en `errors_total{route="/audio"}`.
- Deuda anotada: normalizar el orden cronológico completo de `HISTORIAL_PR` en una próxima orden.

## 2025-12-17 – Kaizen Guardrails + Storage hardening + Stats agregados sin PII

- Se endurece `scripts/kaizen_validate_order.py` para validar metadata real (no placeholders) y aplicar regla: `diff --git` obligatorio solo cuando `TIPO=CAMBIAR`.
- Se agregan tests `tests/test_kaizen_validate_order.py` para que la calidad de órdenes sea estable y no dependa de “revisar después”.
- Se completa hardening del storage in-memory con tests de bordes: purge disabled + legado sin `expires_at`.
- Se crea `CONTRATO_NEUTRO_AUDIO_STATS_V1.md` e implementa `GET /audio/stats` (solo agregados; sin transcript/reply_text/etc).

## 2025-12-21 – Implementación cliente oficial Munay v1 (dashboard web mínimo)

- Se crea el proyecto frontend en `clients/munay-dashboard/` (React + TypeScript + Vite) como primer cliente oficial del endpoint `/audio`.
- Se agrega documentación técnica `CLIENTE_OFICIAL_MUNAY_TECNICO_V1.md` y variables de entorno `.env.example`.
- No se modifica el contrato HTTP ni el payload JSON de `/audio`; solo se construye el consumidor oficial siguiendo los contratos existentes.
## 2025-12-20 – Diseño cliente oficial Munay (dashboard mínimo)

- Se define `CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md` como contrato del primer cliente oficial de `/audio` (dashboard web mínimo para subir/grabar audio y consumir la API).
- Se documenta la UX mínima en `UX_CLIENTE_OFICIAL_MUNAY_V1.md` y se referencia desde `02_ESTADO_Y_NORTE.md`.
- No se modifica el endpoint `/audio` ni se añade código; es una preparación contracts-first para implementar el cliente oficial en una siguiente orden.

## 2025-12-20 – ROADMAP_CAPA_SUPERIOR_V1 y visión de siguiente paso

- Se crea `ROADMAP_CAPA_SUPERIOR_V1.md` para comparar y priorizar la siguiente capa encima del core `/audio` (dashboards, primer cliente oficial, límites/planes por `X-API-Key`).
- Se documenta en `02_ESTADO_Y_NORTE.md` que la priorización de la capa superior se rige por ese roadmap, sin modificar contratos HTTP ni payloads JSON actuales.
- No se toca código; es una actualización de gobernanza y planificación para consolidar el Bot Neutro como plataforma de voz + LLM multi-tenant.

## 2025-12-20 – Visión de plataforma y contrato API Pública v1

- Se actualiza `02_ESTADO_Y_NORTE.md` para dejar explícito que `bot-neutro`
  es una plataforma API de voz + LLM neutral, pensada para múltiples clientes,
  con Munay como primer consumidor oficial.
- Se crea `CONTRATO_API_PUBLICA_V1.md` describiendo el endpoint `/audio`
  como API Pública v1 (headers, body, respuesta, errores, notas de
  multi-tenant y ejemplos).
- No se modifica código ni contratos JSON existentes; se trata de una
  actualización de gobernanza y documentación para consolidar el Bot Neutro
  como producto vendible. El contrato v1 de `/audio` refleja exactamente
  el comportamiento ya observado en pruebas locales.

## 2025-12-20 – Cierre mini-milestone Audio + LLM M1 (fallback y operación)

- Se documenta en `02_ESTADO_Y_NORTE.md` y `RUNBOOK_LLM.md` el comportamiento del provider OpenAI ante errores de cuota/rate limit (`insufficient_quota` → fallback controlado al stub).
- Se explicita el patrón recomendado de uso freemium/premium y se marca el estado del sistema como “Audio + LLM listo para pruebas con crédito real”.
- No se modifica código: el pipeline `/audio` y las respuestas HTTP permanecen iguales; solo se clarifica la operación ante fallos externos del proveedor.

## 2025-12-20 – Eliminación de sombra local sobre `httpx` para OpenAI LLM

 - Se renombra el paquete local `httpx/` a `httpx_local/` para liberar el nombre `httpx` y permitir que el SDK de OpenAI use la biblioteca oficial de `site-packages`.
- No se modifica el contrato HTTP ni el pipeline `/audio`; solo se elimina el conflicto de import.
- Los tests base (`pytest -q`, `pytest --cov=src --cov-fail-under=80`) y la prueba opt-in `llm_integration` pasan con el SDK de OpenAI usando el `httpx` oficial.

## 2025-12-19 – Prueba opcional `llm_integration` para OpenAI LLM

- Se añade `tests/test_llm_openai_integration.py` con marcador `llm_integration`, gated por `OPENAI_LLM_TEST_ENABLED`, para validar el wiring real de `OpenAILLMProvider.from_env`.
- Se actualiza `docs/02_ESTADO_Y_NORTE.md` y `docs/RUNBOOK_LLM.md` documentando cómo ejecutar la prueba sin impactar el modo stub ni el CI.
- No se modifican contratos HTTP ni el comportamiento observable de `/audio`; los tests base y el coverage permanecen iguales.

## 2025-12-18 – Header `x-munay-llm-tier` y propagación de tier al LLM

- `/audio` acepta el header opcional `x-munay-llm-tier` (`freemium`/`premium`, case-insensitive) y lo normaliza a `context["llm_tier"]`.
- El pipeline de audio propaga la tier al `LLMProvider`, manteniendo default seguro `freemium` cuando falta o es inválida.
- La respuesta stub y el comportamiento para clientes sin el nuevo header permanecen iguales.

# 2025-12-17 – Hardening retención in-memory y gobernanza Kaizen

- Se endurece el parseo de `AUDIO_SESSION_RETENTION_DAYS` con fallback a 30 y clamp a 0 cuando el valor es inválido o negativo.
- Se documentan las variables de entorno en `docs/CONFIG/ENV_VARS.md` y se referencia desde README como fuente de verdad.
- Se añaden tests para validar fallback y clamp de retención en `tests/test_audio_storage_privacidad.py`.
- Se actualiza la plantilla de órdenes Kaizen para exigir diffs, DoD, sección de “NO IMPLEMENTADO” y comandos de verificación obligatorios.

## 2025-12-17 – Política de sesiones de audio v1 (contracts-first + enforcement mínimo in-memory)

- Se crea `CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md` para gobernar privacidad, seguridad, retención y control de acceso de `audio_session`.
- Se actualiza `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md` con `expires_at` y reglas de `list_by_*` que exigen coincidencia de `api_key_id` autenticada.
- Se incorpora `docs/MATRIZ_CUMPLIMIENTO_CONTRATOS.md` para trazar contrato ↔ código ↔ tests.
- Se mantiene el bloqueo: no se exponen endpoints de lectura/listado mientras rige la política.

## 2025-12-17 – Correcciones menores tras auditoría L1 (docs-only)

- Se corrigen referencias a componentes del dashboard en `ORDEN_KAIZEN_L1_AUDITORIA_20251217.md`.
- Se actualiza `README.md` para reflejar que `/audio` está implementado y usa providers stub por defecto (Azure/OpenAI opt-in).
- Se alinean `CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md` y `CONTRATO_API_PUBLICA_V1.md` con error 400 por audio faltante, dejando nota sobre validaciones 422 del frontend.
- Se agregan hallazgos al NORTE (`docs/02_ESTADO_Y_NORTE.md`) y se registra esta orden como actualización de gobernanza L1.

## 2025-12-17 – Orden Kaizen L1 (auditoría contratos vs código)

- Se documenta la auditoría global de gobernanza L1 en `ORDEN_KAIZEN_L1_AUDITORIA_20251217.md`, cubriendo mapa de repo, middlewares/providers/endpoints y cuadro Contrato ↔ Código.
- No se realizan cambios funcionales; se dejan hallazgos de privacidad, seguridad y zonas oscuras para futuras órdenes.

## 2025-12-17 – OpenAI LLM opt-in y selección freemium/premium

- Se añade `OpenAILLMProvider` como proveedor LLM opt-in, activable vía `LLM_PROVIDER=openai` con fallback automático a `StubLLMProvider`.
- Se documenta en `docs/02_ESTADO_Y_NORTE.md` y `docs/CONTRATO_NEUTRO_LLM.md` la selección de proveedor por ENV y el uso de `context["llm_tier"]` (`freemium`/`premium`) sin acoplarlo todavía a la capa HTTP.
- Se crea `docs/RUNBOOK_LLM.md` con instrucciones para operar el LLM en modo stub (CI) y modo OpenAI en local.
- Se actualiza la factoría de providers (`factory.py`) y el wiring del `AudioPipeline` para usar el `LLMProvider` neutral sin alterar el contrato observable de `/audio`.

## 2025-12-17 – LLMProvider neutral consolidado y wiring stub en pipeline de audio

- Se consolida el contrato `LLMProvider` con atributos `provider_id`/`latency_ms` alineados a STT/TTS y firma `generate_reply(transcript: str, context: dict) -> str`.
- Se implementa `StubLLMProvider` determinista que siempre devuelve `"stub reply text"` y mantiene latencia explícita para métricas.
- La fábrica de providers expone la construcción de LLM stub y el `AudioPipeline` sigue usando providers enchufables sin cambiar el contrato de `/audio`.
- No se integra ningún LLM externo; se preserva el modo stub y las respuestas actuales.

## 2025-12-16 – Órdenes de prueba stub vs Azure y mini-milestone LLM

- Se formalizan los comandos oficiales para pruebas en modo stub y con Azure opt-in en `docs/02_ESTADO_Y_NORTE.md` y `RUNBOOK_AZURE_SPEECH.md`, incluyendo limpieza de variables de entorno antes de `--cov`.
- Se refuerza que el coverage (`--cov=src --cov-fail-under=80`) se ejecuta siempre sin dependencias de Azure y que los tests `azure_integration` son opcionales.
- Se documenta el mini-milestone previo a LLM: consolidar el contrato neutral `LLMProvider` (`generate_reply(transcript: str, context: dict) -> str` con `provider_id`/`latency_ms`) antes de integrar proveedores reales.

## 2025-12-15 – Logging Azure Speech y prueba de integración opcional

- Se añaden logs claros en los providers Azure STT/TTS antes del fallback para exponer razones y detalles de cancelación.
- Se crea una prueba de integración opcional (`-m azure_integration`) que usa un WAV real definido por ENV para verificar el camino de STT real.
- Se documenta en `RUNBOOK_AZURE_SPEECH.md` cómo habilitar Azure Speech y ejecutar la prueba; las unitarias siguen siendo stub y deterministas.

## 2025-12-14 – Hardening tests de providers Azure (independientes de entorno real)

- Se ajustan los tests de `factory` para que la ruta de error por ausencia de SDK de Azure se pruebe mediante mocks sobre `_require_sdk`, en lugar de depender de la instalación local del SDK.
- Se añade un test simétrico para STT (`AzureSTTProvider`) que verifica el mismo patrón de fallo.
- Se documenta en el NORTE que los unit tests de providers externos son deterministas y no consultan el entorno real; las pruebas con Azure real se reservarán para una capa de integración futura.

## 2025-12-13 – Azure Speech real (opt-in) con fallback a stub

- Se activan las implementaciones reales de `AzureSTTProvider` y `AzureTTSProvider` con import perezoso del SDK de Azure Speech.
- La fábrica falla temprano si faltan credenciales o la librería, manteniendo el modo stub por defecto.
- Ante errores de Azure se degrada automáticamente al stub por petición, reflejando `provider_*` como `azure-*|stub-*`.
- Se documenta la semántica de fallback y se añaden pruebas unitarias para fábricas y pipeline de audio.

## 2025-12-12 – Pipeline de audio enchufable (stub + Azure skeleton)

- Se introduce un orquestador `AudioPipeline` con providers enchufables (STT/TTS/LLM) y selección por variables de entorno (`AUDIO_STT_PROVIDER`, `AUDIO_TTS_PROVIDER`).
- El modo por defecto sigue siendo el stub actual, preservando contratos y tests de `/audio`.
- Se agregan interfaces y factories de providers en `src/bot_neutro/providers/` y un skeleton de `AzureSTTProvider`/`AzureTTSProvider`, activables por ENV para futura integración real con Azure Speech.

## 2025-12-11 – Histograma de latencia para /audio y stub httpx de pruebas

- Se añade `RequestLatencyMiddleware` para medir la duración de cada petición y alimentar el
  histograma de latencia en `InMemoryMetrics.observe_latency`, por ruta.
- `/metrics` ahora exporta buckets `sensei_request_latency_seconds_bucket`, `count` y `sum`
  por ruta, incluyendo `/audio`, alineado con `docs/NEUTRO_SLO_AUDIO_OPERACIONAL.md`.
- Se agrega cobertura de regresión para el histograma de `/audio` en `tests/test_metrics_basic.py`
  verificando la exposición de buckets y agregados en `/metrics`.
- Se incorpora un stub mínimo de `httpx` embebido en el repo, usado únicamente por los tests
  (no se introduce dependencia de `httpx` externo en el runtime).

## 2025-12-10 – SLO audio operativos + queries y alertas (plantillas de referencia)

- Se crea `docs/NEUTRO_SLO_AUDIO_OPERACIONAL.md` con la semántica operativa del SLO de audio, queries PromQL y uso de k6 como validación manual/local.
- Se añaden reglas de alerta de referencia en `docs/prometheus_rules_slo_audio.yml` alineadas a p95 ≤1500 ms, error rate ≤1% y budget burn 85/90/95%.
- Se incorpora el script de carga `tools/load/k6_audio_slo.js` (con `sample_silence.wav`) para estresar `/audio` manualmente sin integrarlo al CI actual.

## 2025-12-09 – Observabilidad y métricas de rate limit

- `CONTRATO_NEUTRO_OBSERVABILIDAD.md` refuerza la lista de métricas núcleo, explicitando incrementos para `sensei_rate_limit_hits_total`, `mem_reads_total`, `mem_writes_total` y los contadores por ruta.
- `CONTRATO_NEUTRO_RATE_LIMIT.md` aclara que cada 429 mantiene los headers `X-Outcome`/`X-Outcome-Detail` y aumenta `sensei_rate_limit_hits_total`.
- `metrics_runtime.py`, `rate_limit.py`, `audio_storage_inmemory.py` y `/metrics` instrumentan los nuevos contadores; las pruebas cubren rechazos 429 y operaciones de memoria conforme al diagnóstico DESCUBRIR.

## 2025-12-08 – Blindaje de redacción de órdenes y bootstrap SKB

- Se refuerza `CONTRATO_SKB_GOBERNANZA.md` con reglas NORTE_version_no_inventada, diferenciación CI_REAL/CI_FUTURO, definición explícita de L1/L2/L3, referencia obligatoria al último DESCUBRIR y catálogo de artefactos de IA prohibidos.
- `MUNAY_GOB_GLOBAL.md` incorpora principios anti-alucinación y la obligación de declarar la gobernanza local que los hereda.
- `CONTRATO_NEUTRO_CONTRIBUCION.md` añade checklist de realidad del NORTE, CI real y limpieza de tokens de IA.
- Se crea `PLANTILLA_ORDEN_EJECUCION_KAIZEN.md` con campos NORTE_VERSION_ACTUAL, referencia a DESCUBRIR y separación CI_REAL/CI_FUTURO.
- `BOOTSTRAP_SKB_HILO.md` ordena que la primera respuesta DESCUBRIR cite la versión real del NORTE y trate referencias inventadas a NORTE/SLOs/CI como BLOQUEO.

## 2025-12-07 – Refinos bootstrap SKB y gobernanza global/local

- `docs/BOOTSTRAP_SKB_HILO.md` ahora declara memoria cero explícita en el mensaje semilla e incluye los contratos de gobernanza (`CONTRATO_SKB_GOBERNANZA.md`, `MUNAY_GOB_GLOBAL.md`) en la fuente de verdad.
- `docs/CONTRATO_SKB_GOBERNANZA.md` clarifica que los bloqueos `ci_rota_*` evalúan la rama `main` y referencia su alineación con `MUNAY_GOB_GLOBAL.md`.
- `docs/MUNAY_GOB_GLOBAL.md` exige que cada repo Munay defina un contrato de gobernanza local (`*_GOB_LOCAL.md` o equivalente) derivado de los principios globales.

## 2025-12-06 – Bootstrap SKB, bloqueos y gobernanza global

- Se crea `docs/BOOTSTRAP_SKB_HILO.md` como mensaje semilla y protocolo oficial para hilos nuevos con SKB.
- Se extiende `docs/CONTRATO_SKB_GOBERNANZA.md` con principios de memoria cero, protocolo de arranque y catálogo de bloqueos automáticos, incluyendo manejo de órdenes multi-tema.
- Se crea `docs/MUNAY_GOB_GLOBAL.md` como contrato base de gobernanza global para futuras repos Munay.

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
    - El propio NORTE (`docs/02_ESTADO_Y_NORTE.md`),
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
  - `{ "detail": "rate limit exceeded" }`
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
