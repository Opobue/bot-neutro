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

## Prueba de integración real con OpenAI (llm_integration)
1. Configura el entorno:

   ```powershell
   $env:LLM_PROVIDER = "openai"
   $env:OPENAI_API_KEY = "<TU_API_KEY_OPENAI>"
   $env:OPENAI_MODEL_FREEMIUM = "gpt-4.1-mini"
   $env:OPENAI_LLM_TEST_ENABLED = "1"
   ```

2. (Opcional) Verifica `/audio` en local con OpenAI activo si quieres confirmar el wiring completo.
3. Ejecuta la prueba dedicada:

   ```powershell
   python -m pytest -m llm_integration -q
   ```

4. Resultado esperado:

   - `1 passed` cuando OpenAI responde correctamente.
   - `0 tests ran` o `skipped` si `OPENAI_LLM_TEST_ENABLED` no está en `"1"` o faltan credenciales.

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

- Manejo de errores de cuota / rate limit:
  - Si la cuenta de OpenAI no tiene crédito o excede su cuota, el SDK puede devolver HTTP 429 con código `insufficient_quota`.
  - En ese caso, el provider captura la excepción, registra un warning `openai_llm_error` y usa el stub como fallback.
  - El cliente sigue recibiendo `200 OK` con `reply_text` generado por el stub y `usage.provider_llm = "openai-llm|stub-llm"` (o similar).
  - Esto es intencional: el Bot Neutro nunca se cae por temas de facturación externa; simplemente degrada a modo stub.

- Patrón de operación recomendado:
  - Mantener `OPENAI_MODEL_FREEMIUM` apuntando a un modelo económico (ej. `gpt-4.1-mini`) para la mayoría de llamadas.
  - Reservar `OPENAI_MODEL_PREMIUM` (ej. `gpt-4.1`) para casos en que el cliente envía `x-munay-llm-tier: Premium`.
  - Validar periódicamente en el panel de OpenAI que exista crédito suficiente antes de pruebas intensivas.

- Estado actual del milestone:
  - El pipeline `/audio` funciona en modo stub sin depender de OpenAI.
  - La integración real OpenAI está verificada hasta el punto de manejo de errores de cuota; las respuestas “full LLM” dependen únicamente de que haya crédito disponible en la cuenta.
