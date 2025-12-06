# SLO Operacionales para /audio (plantilla de referencia)

> **Estado:** Plantilla de referencia. El wiring real a Prometheus/Alertmanager se definirá en una orden L3 o ADR futuro.

## 1. Resumen de SLO oficiales (NORTE v2.1)
- Latencia p95 de `/audio` ≤ **1500 ms**.
- Error rate máximo de `/audio` ≤ **1%**.
- Uptime objetivo: **99.9%**.
- Alertas de budget burn al **85% / 90% / 95%** del presupuesto de errores/latencia.

## 2. Definición operativa
- **Ventanas de observación sugeridas**: 5m (rápida) y 1h (estabilidad), manteniendo coherencia con CI_REAL.
- **Métricas base** (expuestas por `metrics_runtime`):
  - `sensei_request_latency_seconds_bucket{route="/audio"}` (histograma seconds).
  - `sensei_requests_total{route="/audio"}` (counter).
  - `errors_total{route="/audio"}` (counter).
  - `sensei_rate_limit_hits_total` (counter global de rechazos 429 en `/audio`).
- **Nota sobre extensiones futuras**: si en el futuro se añade un label `status` a `errors_total` (por ejemplo, `errors_total{route="/audio",status="5xx"}`), se podrán distinguir explícitamente los 429 del resto. Esa extensión requerirá un contrato o ADR adicional antes de usarse en producción.
- **Errores contados en el SLO**: 4xx/5xx. Las respuestas 429 pueden excluirse del denominador si se quiere medir pureza de negocio; se documentan ambas variantes en las queries.
- **Latencia**: se evalúa con p95; valores >1500 ms violan el SLO.
- **Alcance**: Solo `/audio`. El resto de rutas puede usar las mismas plantillas ajustando la label `route`.

## 3. Queries de monitoreo (PromQL)
> Estas queries son plantillas de referencia copy-pasteables. La integración real depende del stack Prometheus que se defina en una orden futura (L3/ADR).

- **Latencia p95 de /audio** (ventana 5m):
  ```promql
  histogram_quantile(
    0.95,
    sum(rate(sensei_request_latency_seconds_bucket{route="/audio"}[5m])) by (le)
  )
```

* **Error rate /audio** (incluyendo 429):

  ```promql
  sum(rate(errors_total{route="/audio"}[5m]))
    /
  sum(rate(sensei_requests_total{route="/audio"}[5m]))
  ```
* **CI_FUTURO – Error rate /audio excluyendo 429** (requiere un label futuro `status` en `errors_total`):

  ```promql
  sum(rate(errors_total{route="/audio",status!="429"}[5m]))
    /
  sum(rate(sensei_requests_total{route="/audio"}[5m]))
  ```
* **Tasa de rate-limit /audio** (counter global del middleware de `/audio`):

  ```promql
  sum(rate(sensei_rate_limit_hits_total[5m]))
  ```

## 4. Reglas de alerta (referencia)

> Implementadas como ejemplo en `docs/prometheus_rules_slo_audio.yml`. No se despliegan automáticamente.

Principios:

* **Violación SLO de latencia**: p95 > 1.5s sostenido (for 10m).
* **Violación SLO de error rate**: error_rate > 1% sostenido.
* **Budget burn**: alertas al 85/90/95% del presupuesto permitido (1% de errores, 1500ms de latencia p95). Se usan umbrales directos para simplificar la lectura.

## 5. Prueba de carga manual para /audio (k6)

> El script es solo para validación manual/local. **No** se invoca desde los workflows actuales (`ci_tests.yml`, `validate_norte.yml`).

Archivo: `tools/load/k6_audio_slo.js` (usa `tools/load/sample_silence.wav`).

Ejemplo de ejecución local (desde la raíz del repo, con el backend corriendo en `localhost:8000`):

```bash
k6 run \
  -e API_BASE_URL=http://localhost:8000 \
  -e API_KEY=YOUR_API_KEY \
  -e RPS=10 \
  -e TEST_DURATION=2m \
  tools/load/k6_audio_slo.js
```

Notas:

* Ajusta `RPS`, `TEST_DURATION` y `VUS` según la capacidad del entorno. Valores bajos (p.ej. RPS=5, duración 30s) son seguros para desarrollo.
* El script reporta métricas de cliente (`audio_client_latency_ms`, `audio_client_errors`) y respeta los headers `X-API-Key` y `X-Correlation-Id`.
* Mientras corre, observa `/metrics` para validar incrementos de `sensei_requests_total`, `errors_total` y `sensei_rate_limit_hits_total`.

## 6. Próximos pasos (orden L3/ADR sugerida)

* Definir despliegue real de Prometheus/Alertmanager usando estas plantillas.
* Evaluar integración opcional del k6 de carga en un pipeline CI_FUTURO.
* Formalizar en un ADR la semántica definitiva de exclusión/inclusión de 429 para el SLO de error rate.

