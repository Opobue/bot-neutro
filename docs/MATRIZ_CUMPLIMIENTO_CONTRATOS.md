# Matriz de Cumplimiento de Contratos

| Contrato | Código (archivo(s)/módulo(s)) | Estado | Evidencia (tests/paths) |
| --- | --- | --- | --- |
| CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md | `src/bot_neutro/audio_storage_inmemory.py` | OK | `tests/test_audio_storage_privacidad.py`, `tests/test_audio_contract.py`, `tests/test_audio_pipeline_orchestrator.py` |
| CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md | `src/bot_neutro/audio_storage_inmemory.py` | OK (enforcement de storage; sin endpoints de lectura aún) | `tests/test_audio_storage_privacidad.py` |
| CONTRATOS_NEUTRO_AUDIO_PIPELINE/NEUTRO_AUDIO | `/audio` handler y pipeline en `src/bot_neutro/api.py`, `src/bot_neutro/audio_pipeline.py` | OK | `tests/test_audio_contract.py`, `tests/test_audio_pipeline_orchestrator.py`, `tests/test_metrics_observability.py` |
| CONTRATO_NEUTRO_AUDIO_STATS_V1.md | `/audio/stats` en `src/bot_neutro/api.py` | OK | `tests/test_audio_stats_contract.py` |
