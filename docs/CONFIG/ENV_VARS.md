# ENV_VARS – Bot Neutro / Munay

Este documento es la fuente de verdad de variables de entorno soportadas por el runtime.

## Audio sessions (storage persistente)

### AUDIO_SESSION_RETENTION_DAYS
- Tipo: int
- Default: 30
- Regla: si el valor no es parseable → fallback 30. Si es < 0 → clamp a 0. Si es > 30 → clamp a 30.
- Efecto: `expires_at = created_at + retention_days` (si retención 0, expira inmediato).

### AUDIO_SESSION_PURGE_ENABLED
- Tipo: flag (string)
- Default: "1"
- Regla: si es "0" → deshabilita purga automática; cualquier otro valor → habilita.
- Efecto: al crear o listar, el repo elimina sesiones con `expires_at <= now`.

### AUDIO_SESSION_PERSIST_TRANSCRIPT
- Tipo: flag (string)
- Default: "0"
- Regla: si es "1" → persiste `transcript`; por defecto se omite.
- Efecto: cuando está habilitado, `expires_at = min(created_at + 1 día, created_at + AUDIO_SESSION_RETENTION_DAYS)`.

### AUDIO_SESSION_PERSIST_REPLY_TEXT
- Tipo: flag (string)
- Default: "0"
- Regla: si es "1" → persiste `reply_text`; por defecto se omite.
- Efecto: cuando está habilitado, `expires_at = min(created_at + 1 día, created_at + AUDIO_SESSION_RETENTION_DAYS)`.

### AUDIO_SESSION_STORAGE_PATH
- Tipo: string (path)
- Default: `/tmp/bot_neutro_audio_sessions.json`
- Efecto: path del archivo JSON donde se persisten las sesiones.

### AUDIO_STATS_MAX_SESSIONS
- Tipo: int
- Default: 20000
- Regla: si el valor no es parseable → fallback 20000. Si es < 0 → clamp a 0.
- Efecto: límite superior de sesiones a inspeccionar en `/audio/stats` para calcular agregados por tenant.

## Notas de privacidad
- No existen endpoints HTTP de lectura/listado de sesiones mientras rige `CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`.
