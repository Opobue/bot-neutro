# Contrato Neutro de Rate Limit

Define la semántica de control de tráfico para el Bot Neutro, incluyendo rutas excluidas y comportamiento al alcanzar el límite.

## Allowlist permanente
- `/metrics`
- `/healthz`
- `/readyz`

Estas rutas no están sujetas a rate limit para garantizar monitoreo y liveness.

## Configuración
- Controlado por variables de entorno existentes (ejemplos): `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_BURST`.
- Cuando está habilitado, aplica a `/audio`, `/text`, `/actions` u otras rutas no allowlisted.

## Respuesta ante límite alcanzado
- **Código**: `429 Too Many Requests`.
- **Headers**:
  - `X-Outcome: error`
  - `X-Outcome-Detail: rate_limit`
- **Body**: mensaje de error genérico, manteniendo la forma actual de la API.

## Observabilidad
- Cada rechazo incrementa `sensei_rate_limit_hits_total` en `/metrics`.
- Los eventos de rate limit deben reflejarse en logs JSON estructurados.

## Compatibilidad con tests actuales
- La allowlist de `/metrics`, `/healthz` y `/readyz` coincide con las expectativas validadas por los tests de rate limit.
- El código 429 y los headers `X-Outcome`/`X-Outcome-Detail` replican las aserciones de la suite existente.
- No se modifica lógica de runtime, por lo que `pytest -q` y `pytest -k metrics -q` permanecen en verde.
