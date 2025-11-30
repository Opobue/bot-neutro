# Contrato Neutro de Eventos

Define los eventos lógicos que el Bot Neutro debe reconocer y reflejar en observabilidad y logging.

## Eventos lógicos principales
- **Request recibido**: entrada a cualquier endpoint (`/audio`, `/text`, `/actions`, health checks).
- **Respuesta generada**: resultado exitoso de LLM o acción.
- **Error de proveedor**: fallos de STT/TTS/LLM u otras dependencias.
- **Rate limit alcanzado**: request bloqueado por límites configurados.
- **Validación fallida**: errores de formato o contenido en la solicitud.

## Representación
- **Logs JSON**: incluyen `event_type`, `corr_id` (poblado desde el header `X-Correlation-Id`), `outcome`, ruta y metadatos relevantes.
- **Métricas Prometheus**: contadores y histogramas reflejan volúmenes, errores y latencias por evento/ruta.

## Extensión futura
- Colas, webhooks u otros sistemas de mensajería deberán alinearse con estos eventos lógicos para mantener coherencia de trazas y métricas.

## Compatibilidad con tests actuales
- Los eventos de rate limit y errores se reflejan en los contadores que la suite valida (`errors_total`, `sensei_rate_limit_hits_total`).
- La generación de respuestas exitosas y su latencia están cubiertas por los histogramas verificados en tests de métricas.
- No introduce nuevas rutas ni cambios de comportamiento, asegurando que la suite existente siga pasando en verde.
