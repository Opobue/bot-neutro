# Contrato Neutro de Observabilidad

Define la exposición de métricas y expectativas de SLO para el Bot Neutro. Las implementaciones deben mantener compatibilidad con el endpoint `/metrics` y las métricas núcleo ya presentes.

## Endpoint `/metrics`
- **Método**: `GET`
- **Contenido**: `content-type: text/plain; version=0.0.4; charset=utf-8` (formato Prometheus).
- **Rol**: única fuente de scrape para Prometheus y dashboards.
- **Allowlist**: excluido de rate limit para no bloquear monitoreo.

## Métricas núcleo expuestas
- **Histogram de latencia**: `sensei_request_latency_seconds_bucket` con etiquetas por ruta.
- **Contadores de errores**: `errors_total` categorizado por tipo o ruta.
- **Rate limit**: `sensei_rate_limit_hits_total` para registrar rechazos 429.
- **Memoria y operaciones**: `mem_reads_total`, `mem_writes_total` y métricas afines.
- **Requests por ruta**: `sensei_requests_total{route=...}` para volumen y perfil de tráfico.

## SLOs orientativos
- **Latencia audio p95**: `audio_p95_ms ≤ 1500 ms`.
- **Error rate máximo**: `error_rate_max ≤ 1%`.
- **Uptime objetivo**: `uptime_target ≥ 99.9%`.
- **Alertas de budget burn**: disparo en 85% / 90% / 95% del presupuesto de errores o latencia.

## Relación con rate limit y eventos
- Los rechazos por rate limit incrementan `sensei_rate_limit_hits_total` y deben emitirse como eventos de `rate_limit alcanzado`.
- Los fallos de proveedores o validaciones se reflejan en `errors_total` y en logs JSON.

## Compatibilidad con tests actuales
- El `content-type` especificado coincide con las aserciones de la suite de métricas (`pytest -k metrics`).
- Las métricas listadas corresponden a las que los tests validan en payloads Prometheus (latencia, contadores y rate limit).
- El allowlist de `/metrics` mantiene el comportamiento comprobado por los tests de rate limit y disponibilidad.
