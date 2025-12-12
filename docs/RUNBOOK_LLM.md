# RUNBOOK — LLM (stub vs OpenAI opt-in)

Guía para operar el LLM del Bot Neutro en modo determinista (stub) o activando OpenAI de forma opt-in.

## Variables de entorno
- `LLM_PROVIDER`: `stub` (default) o `openai`.
- `OPENAI_API_KEY`: clave de OpenAI (obligatoria en modo OpenAI).
- `OPENAI_BASE_URL`: URL opcional para proxys/gateways compatibles.
- `OPENAI_MODEL_FREEMIUM`: modelo base (ej. `gpt-4.1-mini`).
- `OPENAI_MODEL_PREMIUM`: modelo premium (ej. `gpt-4.1`). Si falta, se reutiliza el freemium.
- `OPENAI_TIMEOUT_SECONDS`: (opcional) timeout en segundos para la llamada al LLM.

## Ejemplos de configuración (PowerShell)

Activar OpenAI:
```powershell
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "<TU_API_KEY_OPENAI>"
$env:OPENAI_MODEL_FREEMIUM = "gpt-4.1-mini"
$env:OPENAI_MODEL_PREMIUM = "gpt-4.1"
# Opcional
$env:OPENAI_BASE_URL = "https://mi-gateway-openai"
$env:OPENAI_TIMEOUT_SECONDS = "30"
```

Volver a modo stub (seguro para CI):
```powershell
Remove-Item Env:LLM_PROVIDER, Env:OPENAI_API_KEY, Env:OPENAI_BASE_URL, Env:OPENAI_MODEL_FREEMIUM, Env:OPENAI_MODEL_PREMIUM, Env:OPENAI_TIMEOUT_SECONDS -ErrorAction SilentlyContinue
```

## Probar `/audio` en local (OpenAI activo)
1. Levanta la API:
   ```powershell
   uvicorn bot_neutro.api:app --reload
   ```
2. Llama al endpoint con un audio claro (ejemplo en PowerShell con `curl.exe`):
   ```powershell
   curl.exe -X POST "http://127.0.0.1:8000/audio" -H "x-api-key: changeme" -F "audio_file=@C:\ruta\a\audio.wav;type=audio/wav"
   ```
3. En la respuesta, valida:
   - `reply_text` distinto de `"stub reply text"`.
   - `usage.provider_llm` mostrando `openai-llm` (o `openai-llm|stub-llm` si se usó fallback).

## Notas
- Los tests unitarios y de cobertura (`pytest -q`, `pytest --cov=src --cov-fail-under=80`) se ejecutan siempre en modo stub sin depender de OpenAI ni de red.
- Si `LLM_PROVIDER` tiene un valor desconocido, el sistema registra un warning y cae a `StubLLMProvider`.
- La selección de modelo freemium/premium se controla vía `context["llm_tier"]`; si no se envía, se asume `"freemium"`.
