# CONTRATO NEUTRO AUDIO STORAGE – ESCALABILIDAD (DESCUBRIR)

**Estado:** DESCUBRIR (no vinculante aún)

## 0) Propósito
Establecer una línea base reproducible de rendimiento del storage de sesiones de audio y
proponer métricas contractuales de escalabilidad para la fase DECIDIR, sin modificar runtime.

## 1) Contratos habilitantes
- `docs/CONTRATO_SKB_GOBERNANZA.md` (D→D→C, no mezclar fases)
- `docs/02_ESTADO_Y_NORTE.md` (NORTE v2.1: SLOs + UI como contrato)
- `docs/CONTRATO_NEUTRO_CONTRIBUCION.md` (checks y disciplina de PR)
- `docs/CONTRATO_NEUTRO_AUDIO_STORAGE_PRIVACIDAD.md` (contexto de storage y retención)

## 2) Contexto técnico y riesgo
El storage actual usa `FileAudioSessionRepository` (`src/bot_neutro/audio_storage.py`):
- `create()` ejecuta `purge_expired()` y luego `_persist()` en cada sesión.
- `_persist()` serializa y reescribe el JSON completo con todas las sesiones.

**Hipótesis de complejidad:** O(N) por operación de persistencia (y O(N²) total al insertar N sesiones).

**Riesgo:** el crecimiento de latencia en el storage puede tensionar los SLOs del NORTE
(`audio_p95_ms=1500`) si el costo de persistencia se acerca al presupuesto por sesión.

## 3) Benchmark reproducible (DESCUBRIR)
Comando reproducible:
```
python scripts/benchmarks/bench_audio_storage.py --sessions 5000 --runs 3
```

Reglas:
- Script sin dependencias nuevas.
- No modifica runtime; instancia directamente el repositorio de storage.
- Limpia directorio temporal al finalizar (salvo `--keep-tmp`).
- Este benchmark no corre en CI; está pensado para ejecución manual.
- Quick run recomendado: `--sessions 1000 --runs 1`.

## 4) Línea base (medición real)
Fuente: `docs/benchmarks/storage_baseline.json` (timestamp: 2026-01-04T20:43:26Z)

**Resumen (promedios en 3 runs, 5000 sesiones, payload≈1024 bytes):**
- p50 create: **43.29 ms**
- p95 create: **128.55 ms**
- Throughput: **20.98 sesiones/seg**
- Tiempo total (5000 sesiones): **247.64 s**
- Tamaño final del archivo: **7,487,780 bytes (~7.49 MB)**

Nota: los resultados varían por hardware/FS; el baseline sirve como referencia y debe compararse con el mismo perfil de ejecución.

## 5) Métricas contractuales propuestas (para DECIDIR)
- **Latencia p95 persistencia por sesión:** objetivo ≤ **250 ms** con **N=5000** sesiones.
- **Capacidad mínima sin degradación crítica:** **N ≥ 5000** sesiones con throughput ≥ **10 sesiones/seg**.
- **Regla de medición:** ejecutar el benchmark con el comando exacto de la sección 3.

> Nota: estos umbrales son propuestas para discusión en DECIDIR; no son vinculantes en DESCUBRIR.

## 6) Opciones a evaluar en DECIDIR (sin decisión)
- **SQLite (un archivo)** con índices mínimos para sesiones.
- **Un archivo por sesión** (sharding simple por id/fecha).
- **Backend pluggable** manteniendo interfaz estable y contratos actuales.

## 7) No metas
- No se cambia runtime en esta fase.
- No se reemplaza storage actual por SQLite en DESCUBRIR.
