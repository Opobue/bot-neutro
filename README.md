# bot-neutro

## Descripción
bot-neutro es un núcleo contract-first basado en FastAPI que expone los endpoints:

- `GET /healthz`
- `GET /readyz`
- `GET /version`
- `GET /metrics`
- `POST /audio` (implementado): acepta `multipart/form-data` con `audio_file` y devuelve JSON con `transcript`, `reply_text`,
  `usage.*` y `session_id`. El modo por defecto usa providers stub; Azure STT/TTS y OpenAI LLM son opt-in vía variables de
  entorno. Consulta los contratos en `docs/CONTRATO_API_PUBLICA_V1.md` y `docs/CONTRATO_CLIENTE_OFICIAL_MUNAY_V1.md`.

Este repositorio es la base neutra a partir de la cual se clonarán bots específicos (por ejemplo, Munay), respetando los contratos definidos en `docs/CONTRATO_NEUTRO_*.md`.

## Instalación local
```bash
git clone https://github.com/Opobue/bot-neutro.git
cd bot-neutro
python -m venv .venv
source .venv/bin/activate  # o .\.venv\Scripts\Activate.ps1 en Windows
pip install -e .[dev]
pytest -q
```

## Ejecución del servidor
```bash
uvicorn bot_neutro.api:app --reload --port 8001
```

Luego puedes probar en:

- http://localhost:8001/healthz
- http://localhost:8001/readyz
- http://localhost:8001/version
- http://localhost:8001/metrics

## Contratos Neutro
Los contratos y el diseño contract-first viven en `docs/CONTRATO_NEUTRO_*.md` y `docs/NEUTRO_OVERVIEW.md`. Este núcleo servirá como base para bots específicos como Munay.

## Audio session retention (in-memory)

El runtime guarda sesiones de audio en memoria para observabilidad interna y debugging local. Por política de privacidad, no existen endpoints HTTP de lectura/listado mientras rige `CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md`.

Variables de entorno:
- `AUDIO_SESSION_RETENTION_DAYS` (default 30): días de retención para calcular `expires_at`.
- `AUDIO_SESSION_PURGE_ENABLED` (default 1): si es "0" deshabilita la purga automática; cualquier otro valor la habilita.

Fuente de verdad de configuración: `docs/CONFIG/ENV_VARS.md`.
