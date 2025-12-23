# CONTRATO_NEUTRO_SESIONES_STORAGE_V1

## A) Meta
**Propósito.** Definir el contrato formal para el almacenamiento, retención y acceso de sesiones de audio del endpoint `/audio`, cumpliendo la privacidad y el NORTE.

**Alcance.** Una “sesión” es el registro lógico asociado a una ejecución de `/audio`, incluyendo identificadores, timestamps, estado y métricas de uso. Este contrato aplica a cualquier repositorio/almacenamiento que guarde sesiones y a cualquier futura lectura de las mismas.

**Fuera de alcance.** Implementación técnica, proveedores específicos, UI/cliente, endpoints de lectura/listado y migraciones de código.

**Referencias.**
Estas referencias deben existir en el repositorio y permanecer alineadas. Si alguna referencia no existe o cambió de nombre, este contrato debe corregirse (PR correctivo inmediato) antes de considerarse “cumplido”.
- `docs/CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`
- `docs/CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`
- `docs/CONTRATO_NEUTRO_AUDIO_STATS_V1.md`
- `docs/CONTRATO_NEUTRO_HEADERS.md`

---

## B) Principios y garantías
- **Privacy-first:** la sesión solo persiste el mínimo necesario; los campos sensibles son opcionales y restringidos.
- **No PII por defecto:** cualquier metadato cliente debe estar sanitizado y libre de PII explícita.
- **`X-API-Key` nunca se persiste:** `api_key_id` siempre se deriva server-side como `sha256(X-API-Key)` en hex truncado a 12 chars.
- **`corr_id` obligatorio:** toda sesión debe incluir `corr_id` para trazabilidad end-to-end.

---

## C) Modelo de datos (contractual)
**Identificadores**
- `session_id` (string, requerido): identificador de la sesión. Mapea al `id` de `audio_session` en `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`.
- `corr_id` (string, requerido): correlation id recibido en el request.
- `api_key_id` (string, requerido): derivado, nunca provisto por el cliente.

**Timestamps**
- `created_at` (timestamp, requerido).
- `expires_at` (timestamp, requerido).

**Estado de sesión**
- `status` (string, opcional): `created` | `processed` | `failed` | `purged`.

**Contenido permitido (opcional y condicionado por privacidad)**
- `transcript` (string, opcional): **sensible**. **DEFAULT: NO se persiste**. Solo puede persistirse en L2 con configuración explícita habilitada (sin especificar nombre en este contrato) y **MUST** cumplir TTL máximo sensible (ver Retención).
- `reply_text` (string, opcional): **sensible**. **DEFAULT: NO se persiste**. Solo puede persistirse en L2 con configuración explícita habilitada (sin especificar nombre en este contrato) y **MUST** cumplir TTL máximo sensible (ver Retención).
- `usage` (objeto, requerido):
  - `input_seconds` (number)
  - `output_seconds` (number)
  - `stt_ms` (int)
  - `llm_ms` (int)
  - `tts_ms` (int)
  - `total_ms` (int)
  - `providers` (objeto): `stt`, `llm`, `tts` (string).
- `client_meta` (objeto, opcional): metadatos de cliente **sin PII**. Si se detecta PII, **MUST** descartarse o sanitizarse. Equivale a un subconjunto sanitizado de `meta_tags` definido en `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`.

**Contenido prohibido**
- `audio_bytes` persistido (por defecto **NO**).
- Secretos, API keys, tokens o credenciales.
- PII explícita (ejemplos: nombre + apellido, email, teléfono, dirección, documento, salud/finanzas).

**Nullability**
- Campos requeridos: `session_id`, `corr_id`, `api_key_id`, `created_at`, `expires_at`, `usage`.
- Campos opcionales: `status`, `transcript`, `reply_text`, `client_meta`.

---

## D) Retención y expiración (TTL)
- `expires_at` **MUST** existir en cada sesión nueva.
- Retención configurable por ENV (a implementar en L2):
  - `AUDIO_SESSION_RETENTION_DAYS` (entero, default 30).
  - `AUDIO_SESSION_PURGE_ENABLED` (1/0).
- Si `AUDIO_SESSION_RETENTION_DAYS=0` → `expires_at = created_at` (expiración inmediata) y la sesión **no** debe contarse como retenida.
- Para campos sensibles (`transcript`, `reply_text`) el TTL máximo **MUST** ser ≤ 1 día.
- Si `transcript` y/o `reply_text` se persisten (configuración explícita habilitada), `expires_at` **MUST** calcularse como `min(created_at + 1 día, created_at + AUDIO_SESSION_RETENTION_DAYS días)`.
- **Purga:** proceso interno, sin endpoint público. Debe eliminar sesiones con `expires_at <= now` y reportar métricas (declarativo).
- **Legacy:** sesiones sin `expires_at` se consideran expiradas para evitar retención indefinida (ver política de privacidad).
- **Purga deshabilitada:** si `AUDIO_SESSION_PURGE_ENABLED=0`, no hay purga automática, pero `expires_at` sigue siendo obligatorio y **no** se habilitan lecturas/listados.

---

## E) Control de acceso y lectura
- **Bloqueo vigente:** no se exponen endpoints de lectura/listado hasta cumplir el contrato y la política de privacidad.
- Toda lectura futura debe cumplir:
  - Autenticación por `X-API-Key`.
  - Autorización estricta por `api_key_id` derivado (solo dueño).
  - Auditoría con logs correlados por `corr_id`.
- Semántica contractual futura:
  - Si se implementa `GET /audio/sessions/{id}`, **MUST** filtrar por `api_key_id` derivado del request.
  - `transcript`/`reply_text` nunca se exponen a terceros ni a otros tenants.

---

## F) Observabilidad (declarativa)
- Métricas esperadas (nombres sugeridos):
  - `audio_sessions_current` (gauge)
  - `audio_sessions_purged_total` (counter)
  - `errors_total{route=...}` (agregado)
- Logging mínimo para auditoría: `event`, `corr_id`, `api_key_id`, `session_id` (cuando aplique).
- **Nota:** este contrato **no** implementa métricas/logs; solo define el requerimiento.

---

## G) Seguridad
- `api_key_id` se deriva **siempre** desde `X-API-Key` en runtime; nunca se acepta del cliente.
- `client_meta` debe sanitizarse y excluir PII.
- Separación multi-tenant estricta por `api_key_id`.

---

## H) Compatibilidad y migración
- **Estado actual:** almacenamiento persistente local (archivo JSON) con TTL y purga interna.
- **Futuro:** repositorio enchufable (interface) sin romper este contrato.
- **Migración:** cualquier migración futura debe preservar los campos obligatorios, la derivación de `api_key_id` y las reglas de retención/acceso.

---

## I) Checklist de cumplimiento
Antes de habilitar endpoints de lectura/listado, una implementación L2 debe cumplir:
1. `expires_at` obligatorio y cálculo por `AUDIO_SESSION_RETENTION_DAYS`.
2. Purga interna conforme a `AUDIO_SESSION_PURGE_ENABLED`.
3. `api_key_id` derivado desde `X-API-Key` (nunca aceptado del cliente).
4. Aislamiento multi-tenant por `api_key_id` en toda lectura.
5. Logs mínimos con `corr_id` y `api_key_id`.
6. Métricas declaradas para sesiones actuales y purgas.
7. No persistir secretos ni audio bytes por defecto.
8. Por defecto no persistir `transcript`/`reply_text`.
9. Si se habilita persistencia sensible: flags explícitos, TTL máximo 1 día y auditoría.
10. Cumplimiento explícito de `CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`.
