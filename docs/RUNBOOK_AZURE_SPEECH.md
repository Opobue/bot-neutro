# RUNBOOK_AZURE_SPEECH

Guía rápida para habilitar y probar Azure Speech en Bot Neutro.

## Configuración de variables de entorno

Usa el script `set_env_azure_speech.ps1` (o un `.env` equivalente) para definir sin commitear valores sensibles:

- `AUDIO_STT_PROVIDER`: `azure` para activar STT real (default `stub`).
- `AUDIO_TTS_PROVIDER`: `azure` para activar TTS real (default `stub`).
- `AZURE_SPEECH_KEY`: clave de Azure Speech.
- `AZURE_SPEECH_REGION`: región de Azure Speech (ej. `eastus`).
- `AZURE_SPEECH_STT_LANGUAGE_DEFAULT`: locale por defecto para STT (ej. `es-ES`).
- `AZURE_SPEECH_TTS_VOICE_DEFAULT`: voz por defecto para TTS (ej. `es-ES-AlonsoNeural`).
- `AZURE_SPEECH_TEST_WAV_PATH`: ruta local a un WAV válido para la prueba de integración.

Para forzar modo stub (y que cualquier prueba Azure quede `skipped`), limpia las ENV antes de ejecutar tests:

```powershell
Remove-Item Env:AUDIO_STT_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:AUDIO_TTS_PROVIDER -ErrorAction SilentlyContinue
Remove-Item Env:AZURE_SPEECH_KEY -ErrorAction SilentlyContinue
Remove-Item Env:AZURE_SPEECH_REGION -ErrorAction SilentlyContinue
Remove-Item Env:AZURE_SPEECH_STT_LANGUAGE_DEFAULT -ErrorAction SilentlyContinue
Remove-Item Env:AZURE_SPEECH_TTS_VOICE_DEFAULT -ErrorAction SilentlyContinue
Remove-Item Env:AZURE_SPEECH_TEST_WAV_PATH -ErrorAction SilentlyContinue
```

## Ejecución de pruebas

Las pruebas unitarias siguen usando el modo stub y no requieren Azure:

```bash
python -m pytest -q
python -m pytest --cov=src --cov-fail-under=80
```

> `--cov` se corre siempre en modo stub: no requiere SDK Azure ni internet.

Prueba de integración opcional (solo si se configuraron las variables anteriores y existe el WAV real):

```bash
python -m pytest -m azure_integration -q
```

## Interpretación de resultados y logs

- En modo stub, los providers siguen reportando `stub-stt`/`stub-tts` como `provider_id`.
- En modo Azure, ante fallos el provider degrada al stub y el `provider_id` queda como `azure-stt|stub-stt` o `azure-tts|stub-tts`.
- Cuando Azure falla, se emiten logs con `azure_stt_error`/`azure_tts_error` (y variantes `*_canceled`/`*_no_match`) describiendo la razón y detalles de cancelación.
