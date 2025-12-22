# NORTE MUNAY v2.1 — Estado y Principios Operativos

## 1. Principio Supremo
El proyecto Munay/SenseiKaizen debe avanzar sin contradicciones, sin retrocesos, sin redefinir decisiones previamente aprobadas.
Toda modificación debe pasar por una **ORDEN KAIZEN** (L1, L2 o L3).

## 2. Gobernanza del Proyecto
El proyecto sigue un modelo **Contracts-First**, con la siguiente secuencia OBLIGATORIA:

1. Actualizar los contratos en `/docs/`
2. Actualizar historial PR
3. Alinear ADRs si aplica
4. recién después tocar código

Los contratos NO se ignoran, NO se contradicen, NO se redefinen sin orden formal.

### Visión de plataforma

* `bot-neutro` es el **núcleo API de voz + LLM neutral**.
* Su objetivo es ofrecer un endpoint HTTP estable que reciba audio y devuelva:

  * transcripción (`transcript`),
  * respuesta del modelo (`reply_text`),
  * audio de respuesta opcional (`tts_url`),
  * métricas de uso (`usage.*`).
* La API está diseñada para ser:

  * consumida por **Munay** como primer cliente oficial,
  * reutilizada por otros proyectos propios del autor,
  * ofrecida como servicio a terceros (empresas, integradores tipo n8n/Make).
* El diseño es **multi-tenant-ready**: el uso real de múltiples clientes se hará por API keys, pero la filosofía ya asume varios consumidores desde el principio.
* La priorización de la siguiente capa encima del core (`dashboards`, `cliente oficial`, `planes por API key`) se detalla en `docs/ROADMAP_CAPA_SUPERIOR_V1.md`. Toda evolución debe alinearse a ese roadmap y actualizar este Norte si hay cambios estructurales.
* El primer cliente oficial definido para `/audio` es un dashboard web mínimo Munay, descrito en
  `docs/CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md` y `docs/UX_CLIENTE_OFICIAL_MUNAY_V1.md`, que actúa como referencia oficial de consumo de la API Pública v1.

### 2.1 Gobernanza SKB y ADRs
- `docs/CONTRATO_SKB_GOBERNANZA.md` es contrato fuente para prompts y órdenes (D→D→C, bloqueos y reglas contracts-first).
- `docs/CONTRATO_NEUTRO_CONTRIBUCION.md` es guía obligatoria para cualquier PR.
- `docs/adr/` contiene los ADRs obligatorios para cambios de arquitectura, seguridad o SLO/SLA; toda decisión usa `ADR_TEMPLATE.md`.
- Pipeline mínimo de CI (no negociable):
  - `.github/workflows/validate_norte.yml`
  - `.github/workflows/ci_tests.yml` (ejecuta `pytest -q` y `pytest --cov=src --cov-fail-under=80`).

---

## 3. SLOs oficiales (audio)
| Métrica | Valor |
|--------|--------|
| **audio_p95_ms** | ≤ 1500 ms |
| **error_rate_max** | ≤ 1% |
| **uptime_target** | 99.9% |
| **budget_burn_alert** | 85/90/95% |

Ver `docs/NEUTRO_SLO_AUDIO_OPERACIONAL.md` para la definición operativa, queries y alertas de referencia del SLO de audio.

Todas las implementaciones deben acercarse a estos límites incluso en pruebas.

---

## 4. UI como contrato
Toda respuesta debe incluir estos headers:

- `X-Outcome`
- `X-Correlation-Id`
- `X-Outcome-Detail` cuando aplica

El sistema debe mantener consistencia absoluta.

---

## 5. Observabilidad
Cada PR debe incluir:

- Métricas Prometheus necesarias  
- Queries PromQL  
- Alertas burn-rate  
- Umbrales alineados al SLO  
- Pruebas (k6 o equivalente)  

---

## 6. Flujo Kaizen (órdenes)

### **L1 — Agregar o corregir archivos de gobierno**
Contratos, NORTE, ADR, CI, runbooks.

### **L2 — Cambios en lógica, endpoints, modelos**
Implementación respetando contratos.

### **L3 — Refactors internos**
Sin cambiar comportamiento observable.

---

## 7. Regla de Coherencia entre Hilos
Cada nuevo hilo debe comenzar con este mensaje:

> Usa SIEMPRE los archivos del repo como verdad absoluta:  
> - `docs/02_ESTADO_Y_NORTE.md`  
> - `docs/HISTORIAL_PR.md`  
> - Todos los contratos NEUTRO  
> - Todos los contratos MUNAY  
> No redefines nada fuera de estos documentos.  
> Todo cambio requiere una ORDEN KAIZEN.

---

## 8. Estado Actual del Sistema (última actualización)
- Pipeline de audio completo con almacenamiento en memoria
- Pipeline de audio con providers enchufables (stub por defecto, Azure seleccionable por ENV)
- Azure Speech STT/TTS real disponible como opt-in local, con fallback automático a stub ante fallos
- LLMProvider neutral consolidado: stub por defecto, proveedores reales activables por ENV (`LLM_PROVIDER`)
- Selección freemium/premium modelada vía `context["llm_tier"]`, ahora alimentada desde la capa HTTP vía header opcional `x-munay-llm-tier` (`freemium`/`premium`, case-insensitive, default seguro `freemium` ante ausencia o valor inválido)
- Tests unitarios de providers externos deterministas y aislados del entorno real:
  - No dependen de SDKs instalados ni credenciales reales.
  - Los errores de dependencia (p. ej. falta de SDK) se validan mediante mocks controlados.
  - Pruebas reales con Azure existen como capa de integración opcional (`-m azure_integration`), nunca obligatoria en CI.
- Headers Munay (`x-munay-user-id`, `x-munay-context`) integrados
- Métricas runtime (`METRICS`) activas
- Rate-limit funcional por API key
- api_key_id persistido en sesiones es derivado sha256[:12]; X-API-Key nunca se persiste
- 100% de pruebas unitarias verdes
- PRs recientes documentados en `HISTORIAL_PR.md`
- Cliente oficial Munay v1 (dashboard web) implementado en `clients/munay-dashboard/`, alineado a `CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md` y `CLIENTE_OFICIAL_MUNAY_TECNICO_V1.md`, con registro en `docs/HISTORIAL_PR.md` (2025-12-21).
- README actualizado para reflejar que `/audio` está implementado (antes indicaba stub 501) y documentar el payload real y modo stub por defecto con providers Azure/OpenAI opt-in.
- Contratos públicos ajustados a error 400 cuando falta audio; el frontend puede mostrar validaciones 422 en la UI, pero el backend responde 400.
- Storage de sesiones sigue siendo in-memory sin endpoints HTTP de lectura/listado; expires_at/purge/enforcement se implementan como mínimo interno en esta orden.
- Política de sesiones definida en `CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md` y aplicada como bloqueo para exponer lecturas/dashboards/persistencia hasta cumplir control de acceso y retención.
- Política de tiers/costos LLM definida en `CONTRATO_NEUTRO_LLM_TIERS_COSTOS_V1.md`: la API-Key es la fuente de verdad, el header `x-munay-llm-tier` es solo `tier_solicitado` y no puede escalar privilegios.
- Pendiente L2 de enforcement: `/audio` debe rechazar tiers superiores al autorizado por API-Key, devolver `X-Outcome-Detail=llm.tier_forbidden`/`llm.tier_invalid` cuando aplique e instrumentar una métrica de denegación de tier (p. ej. `llm_tier_denied_total`) + `errors_total{route="/audio"}` (agregado) y logs correlados.

---

## 9. Pruebas oficiales (stub vs Azure)

### 9.1 Modo stub (base CI y día a día)
- Limpiar ENV antes de probar para forzar stub y que cualquier test `azure_integration` quede `skipped`:

  ```powershell
  Remove-Item Env:AUDIO_STT_PROVIDER -ErrorAction SilentlyContinue
  Remove-Item Env:AUDIO_TTS_PROVIDER -ErrorAction SilentlyContinue
  Remove-Item Env:AZURE_SPEECH_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:AZURE_SPEECH_REGION -ErrorAction SilentlyContinue
  Remove-Item Env:AZURE_SPEECH_STT_LANGUAGE_DEFAULT -ErrorAction SilentlyContinue
  Remove-Item Env:AZURE_SPEECH_TTS_VOICE_DEFAULT -ErrorAction SilentlyContinue
  Remove-Item Env:AZURE_SPEECH_TEST_WAV_PATH -ErrorAction SilentlyContinue
  Remove-Item Env:LLM_PROVIDER -ErrorAction SilentlyContinue
  Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:OPENAI_BASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:OPENAI_MODEL_FREEMIUM -ErrorAction SilentlyContinue
  Remove-Item Env:OPENAI_MODEL_PREMIUM -ErrorAction SilentlyContinue
  ```

- Comandos oficiales:

  ```powershell
  python -m pytest -q
  python -m pytest --cov=src --cov-fail-under=80
  ```

- El header opcional `x-munay-llm-tier` para `/audio` no altera las pruebas base: si no se envía, el pipeline mantiene `freemium` por defecto y el stub sigue devolviendo `"stub reply text"`.

- Regla de oro: `--cov` se ejecuta siempre en modo stub (sin credenciales ni SDK Azure). Este será el paso obligatorio en CI.
- Futuras pruebas reales de LLM usarán un marcador dedicado (p. ej. `llm_integration`) y seguirán siendo opt-in, igual que Azure.

### 9.2 Modo Azure opt-in (integración manual)
- Cargar variables con `. .\set_env_azure_speech.ps1` (fuera de control de versiones) y activar el `.venv`.
- Validar providers reales con:

  ```powershell
  python -m pytest -m azure_integration -q
  ```

- Este bloque es opcional y no afecta al coverage base ni al pipeline CI.

### 9.3 Modo LLM OpenAI opt-in (integración manual)
- Marcador dedicado: `llm_integration`.
- Variables requeridas para habilitar la prueba real:

  - `OPENAI_API_KEY`
  - `OPENAI_MODEL_FREEMIUM`
  - `OPENAI_LLM_TEST_ENABLED=1`

- Ejemplo de ejecución (PowerShell):

  ```powershell
  $env:LLM_PROVIDER = "openai"
  $env:OPENAI_API_KEY = "<TU_API_KEY_OPENAI>"
  $env:OPENAI_MODEL_FREEMIUM = "gpt-4.1-mini"
  $env:OPENAI_LLM_TEST_ENABLED = "1"

  python -m pytest -m llm_integration -q
  ```

- Notas:

  - La prueba es opt-in y queda `skipped` si no se configuran los envs anteriores.
  - Los comandos base (`pytest -q` y `pytest --cov=src --cov-fail-under=80`) siguen ejecutándose en modo stub sin depender de OpenAI ni de red.

---

## 10. Integración LLM
- Contrato `LLMProvider` operativo con stub determinista como default.
- OpenAI disponible como provider opt-in vía `LLM_PROVIDER=openai`, con fallback automático al stub y selección de modelo mediante `context["llm_tier"]` (`freemium`/`premium`).
- Futuras integraciones (Azure OpenAI, modelos locales) seguirán el mismo patrón sin requerir credenciales en CI.
- La elección del proveedor LLM (OpenAI, futuros modelos, etc.) es un detalle interno del Bot Neutro.
- El contrato público `/audio` se mantiene estable: los clientes no necesitan saber qué proveedor hay por debajo, solo confían en:

  * formato de entrada (audio + headers),
  * formato de salida (JSON con `transcript`, `reply_text`, `usage.*`),
  * garantías de fallback (stub) ante fallos externos.
- Regla adicional: no se permiten paquetes locales con nombres que choquen con dependencias críticas (p. ej. `httpx`, `openai`). Cualquier cliente HTTP interno debe vivir bajo un nombre propio (ej. `httpx_local`).

- El detalle de la **API Pública v1** (endpoint `/audio`) se documenta en `docs/CONTRATO_API_PUBLICA_V1.md` y actúa como contrato de producto para clientes externos (incluyendo Munay).

- Comportamiento ante errores de OpenAI:
  - Si el SDK lanza errores de cuota/rate limit (por ejemplo `insufficient_quota`, HTTP 429), el provider registra `openai_llm_error` en logs y cae de forma controlada al `StubLLMProvider`.
  - En esos casos, el endpoint `/audio` sigue devolviendo `200 OK` y la métrica `usage.provider_llm` incluye la cadena de fallback (ej. `openai-llm|stub-llm`).
  - Este patrón garantiza que problemas externos de facturación/cuota no rompan el contrato HTTP ni la experiencia del cliente.

- Patrón de uso recomendado:
  - `freemium` (mini) como tier por defecto para casi todas las llamadas.
  - `premium` solo cuando el cliente envía el header `x-munay-llm-tier: Premium`, de forma explícita y consciente del mayor coste.
  - El mini-milestone actual se considera **“Audio + LLM listo para pruebas con crédito real”**: en cuanto la cuenta disponga de saldo, `/audio` empezará a devolver respuestas reales del LLM sin cambios de código.

---

## 11. Filosofía del Proyecto
- **Máxima claridad**
- **Cero contradicciones**
- **Iteración sin pérdidas de coherencia**
- La IA actúa como arquitecto, no como creativo descontrolado
- Cada avance debe poder reproducirse sin error

---

## 12. Mantenimiento
Toda evolución del proyecto DEBE modificar este archivo.
