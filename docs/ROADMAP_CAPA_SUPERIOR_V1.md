# Roadmap de la capa superior sobre el núcleo Bot Neutro

## 1. Contexto
- Core `/audio` estabilizado como API Pública v1 (`CONTRATO_API_PUBLICA_V1.md`).
- LLM con fallback a stub; proveedores externos son detalles internos con resiliencia por defecto.
- Objetivo: traje neutro reutilizable para múltiples bots y clientes (Munay como primero), listo para operar aun con fallas externas.

## 2. Opciones de siguiente capa

### A. Dashboards/observabilidad
- ¿Qué implicaría?
  - Exponer y consumir métricas clave ya disponibles (`usage.*`, `provider_*`, `corr_id`, histogramas de latencia, contadores de rate-limit, etc.).
  - Diseñar paneles base: llamadas por periodo, latencias p95/p99, `error_rate`, uso por `X-API-Key`, desglose stub vs proveedor real.
  - Documentar queries/alertas mínimas y cómo operarlas (PromQL + k6 como validación).
- Impacto
  - Visibilidad end-to-end del comportamiento del core y salud de SLOs.
  - Base tangible para SLAs y soporte a clientes (incluyendo Munay) con diagnósticos rápidos.
- Esfuerzo aproximado
  - Integrar dashboard de referencia (Grafana/Metabase) y publicar queries recomendadas.
  - Ajustar exportadores/labels si falta granularidad por ruta o API key.

### B. Primer cliente oficial (Munay dashboard o mini CLI)
- ¿Qué implicaría?
  - Construir un cliente humano para `/audio` que permita probar el traje sin intermediarios adicionales.
  - Alternativas: dashboard web mínimo para subir/grabar audio y ver respuesta, o CLI que capture audio local y envíe a `/audio` con headers.
  - Definir flujos básicos: autenticación por `X-API-Key`, selección de `x-munay-llm-tier`, manejo de correlación y visualización de `usage`.
- Impacto
  - Validación UX real del contrato público; feedback inmediato sobre headers, latencias percibidas y mensajes de error.
  - Muestra concreta para Munay y terceros de cómo consumir la API; acelera demos y onboarding.
- Esfuerzo aproximado
  - Diseño ligero de flujos y UX mínima; no requiere acoplar toda la app Munay todavía.
  - Instrumentar el cliente con logs/corr_id para ejercer trazabilidad con el core.

### C. Límites/planes por `X-API-Key`
- ¿Qué implicaría?
  - Diseñar un catálogo de planes (Free/Pro/Enterprise) con cuotas: QPS, minutos de audio/mes, tamaño máximo de archivo, políticas de burst.
  - Definir headers/errores asociados (`X-Outcome-Detail`, mensajes de límite) y reporting de consumo.
  - Borrador de governance para tenants: ciclo de vida de API keys, suspensiones, upgrades y auditoría.
- Impacto
  - Visión clara de negocio API; habilita pricing, multi-tenant real y soporte a socios externos.
  - Prepara al core para monetización y compliance mínima.
- Esfuerzo aproximado
  - Solo diseño/contratos en esta fase: matrices de límites, respuestas esperadas y relación con métricas existentes.
  - Implementación de enforcement vendrá en orden posterior.

## 3. Tabla comparativa de decisión
| Opción | Impacto en Munay | Impacto negocio API | Complejidad técnica inmediata | Desbloqueos futuros | Nota |
| ------ | ---------------- | ------------------- | ----------------------------- | ------------------- | ---- |
| A | Medio: visibilidad y diagnósticos para pruebas internas de Munay. | Alto: fundación para SLAs y soporte formal. | Medio: requiere wiring de dashboards y quizá ajustes de métricas. | Alta: habilita reportes y base para billing/planes. | Ya hay métricas base; falta capa de visualización y queries curadas. |
| B | Alto: UX real para validación y demos de Munay; prueba directa del contrato `/audio`. | Medio: ejemplo oficial acelera adopción de terceros. | Medio-bajo: cliente mínimo sin tocar backend. | Medio: genera feedback para priorizar futuras mejoras de API/observabilidad. | Alinea al traje con uso humano inmediato; reduce incertidumbre UX. |
| C | Medio: clarifica expectativas de uso de Munay como tenant. | Muy alto: define estrategia de monetización y límites. | Bajo-medio: trabajo de diseño contractual; no requiere código inmediato. | Alta: prepara enforcement y reporting comercial. | Depende parcialmente de visibilidad (A) para medir consumo real. |

## 4. Decisión
- **Opción elegida: B. Primer cliente oficial (Munay dashboard o mini CLI).**
- Justificación
  - Proporciona validación real del contrato `/audio` con usuarios humanos y headers oficiales (`X-API-Key`, `x-munay-llm-tier`).
  - Entrega un artefacto demostrable para Munay y terceros, acelerando demos y onboarding sin depender de integraciones completas.
  - Genera feedback directo sobre latencia percibida, mensajes de error y UX, insumos necesarios antes de invertir en dashboards o planes.
  - Requiere menor complejidad técnica inmediata que A, manteniendo el backend intacto.
  - Sirve de referencia viva para futuros clientes, reforzando el traje como plataforma neutral.
- Otras opciones
  - **A. Dashboards/observabilidad:** marcada como **Fase siguiente**; se aprovechará el cliente para validar qué métricas/queries son más útiles.
  - **C. Límites/planes por `X-API-Key`:** marcada como **Fase siguiente**; se diseñará después de contar con señales de uso real y observabilidad mejorada.

## 5. Próxima ORDEN KAIZEN sugerida
- **Título preliminar:** `ORDEN KAIZEN L2 – Primer cliente oficial de /audio (Munay dashboard o mini CLI)`
- Alcance esperado: definir UX mínima, flujos de autenticación por API key, manejo de audio (grabación/subida), headers recomendados y trazabilidad con `corr_id`/`usage`.
