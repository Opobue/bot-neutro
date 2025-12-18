# CONTRATO_NEUTRO_LLM_TIERS_COSTOS_V1

## Propósito y alcance
- Formalizar la gobernanza de tiers LLM en un entorno multi-tenant donde **la API-Key es la fuente de verdad** para determinar el plan autorizado.
- Evitar la escalada unilateral vía header `x-munay-llm-tier`; el header solo es una **solicitud del cliente** que debe validarse contra el plan.
- Establecer la semántica de validación, errores, observabilidad y cuotas/costos **sin implementar todavía la verificación** (se realizará en una orden L2).

## Definiciones
- `tier`: nivel de servicio del LLM. Valores permitidos en V1: `freemium`, `premium`. El contrato es extensible (p. ej. `enterprise`).
- `tier_solicitado`: valor enviado por el cliente en el header `x-munay-llm-tier` (case-insensitive). Si no se envía, se considera ausente.
- `tier_autorizado`: valor determinado **server-side** a partir de la API-Key autenticada. Es la única fuente de verdad.

## Interfaz (request)
- Header opcional `x-munay-llm-tier`:
  - Valores aceptados: `freemium` | `premium` (case-insensitive, se normaliza a minúsculas).
  - Si el header está ausente: se usa `tier_autorizado` por defecto.
  - Si el valor es inválido: se considera **header inválido**. Propuesta de respuesta: `400 Bad Request`, `X-Outcome=error`, `X-Outcome-Detail=llm.tier_invalid`. El estado actual (L1) mantiene compatibilidad degradando a `freemium` para no romper clientes; la validación estricta llegará en L2.

## Fuente de verdad (server-side)
- La API-Key autenticada define el `tier_autorizado` y las cuotas/costos asociadas.
- El header **NO** puede elevar privilegios ni modificar las cuotas; sirve como hint para elegir el modelo dentro del tier autorizado.
- La lógica de validación (L2) debe ejecutarse **antes** de construir el contexto `llm_tier` para el pipeline.

## Reglas de decisión
1) **Header ausente** → usar `tier_autorizado`.
2) **Header presente y válido**:
   - Si `tier_solicitado` ≤ `tier_autorizado` (misma categoría o inferior) → permitido; `context["llm_tier"] = tier_solicitado`.
   - Si `tier_solicitado` > `tier_autorizado` → denegar. Respuesta propuesta: `403 Forbidden`, `X-Outcome=error`, `X-Outcome-Detail=llm.tier_forbidden`.
3) **Header inválido** → proponer `400 Bad Request`, `X-Outcome-Detail=llm.tier_invalid`. (Estado actual: se degrada a `freemium` y sigue la ejecución para no romper contratos previos.)

Nota de orden en V1: `freemium < premium`.

## Respuesta y errores (semántica)
- Headers obligatorios en toda respuesta: `X-Outcome`, `X-Correlation-Id`; `X-Outcome-Detail` cuando aplica un error/bloqueo.
- Códigos/`X-Outcome-Detail` propuestos:
  - `403 Forbidden` + `X-Outcome-Detail=llm.tier_forbidden` cuando el cliente solicita un tier superior al autorizado.
  - `400 Bad Request` + `X-Outcome-Detail=llm.tier_invalid` cuando el header tiene un valor fuera de catálogo.
  - `200 OK` + `X-Outcome` según convención vigente (p. ej. `ok`/`success`) cuando el tier solicitado es aceptado (o ausente y se usa el autorizado).
- Los mensajes de error no deben exponer PII ni la API-Key; se puede incluir un `api_key_id` derivado y `tier_autorizado` en logs internos.

## Observabilidad mínima obligatoria
- **Métrica de denegación**: contador `llm_tier_denied_total{route="/audio", requested_tier, authorized_tier}` que se incrementa cuando `tier_solicitado` > `tier_autorizado`.
- **Errores agregados**: incremento de `errors_total{route="/audio"}` (agregado) en cada denegación.
- **Logs estructurados** (JSON) por request, con al menos: `corr_id` (de `X-Correlation-Id`), `api_key_id` derivado (no secreto), `requested_tier`, `authorized_tier`, `outcome` (`accepted` | `downgraded` | `denied`), `route`.
- **Correlación**: `X-Correlation-Id` debe estar presente siempre; se usa para enlazar métricas, logs y traces.

## Cuotas y costos (política parametrizable)
- Las cuotas se expresan en unidades neutrales para evitar decisiones monetarias prematuras. Referencias iniciales (configurables por env/config en L2):
  - `freemium`: límite diario sugerido de `requests_per_day`, `tokens_per_day`, modelo máximo permitido `freemium`.
  - `premium`: límites superiores o sin tope práctico, con acceso a modelos `premium`.
- Los montos monetarios quedan `TBD` y requieren ADR específico. Este contrato solo fija las unidades y la necesidad de asociarlas a la API-Key.

## Estado de implementación (L1)
- Hoy `/audio` solo normaliza `x-munay-llm-tier` a `context["llm_tier"]` cuando es `freemium|premium` y aplica fallback seguro a `freemium` ante valores faltantes/invalidos.
- **No existe enforcement** contra la API-Key: el header puede solicitar `premium` aunque la key no lo tenga asignado. Esto es el gap a cubrir en L2.
- Métricas y logs de denegación aún no existen; deberán instrumentarse junto con la validación en la orden L2.

## Camino a enforcement (orden L2 futura)
- Implementar la resolución de `tier_autorizado` por API-Key antes de llamar al pipeline.
- Aplicar las reglas de decisión anteriores y devolver los códigos/headers propuestos.
- Instrumentar las métricas `llm_tier_denied_total` e incrementar `errors_total{route="/audio"}` en cada bloqueo.
- Agregar pruebas de runtime (unitarias y contractuales) que cubran: header ausente, tier válido ≤ autorizado, tier superior denegado, header inválido.

## Compatibilidad y bloqueos
- Este contrato no introduce nuevos endpoints ni cambia las firmas existentes; define reglas de validación y observabilidad para futuras implementaciones.
- No debe romper clientes actuales: hasta que se libere L2, el comportamiento observable sigue siendo el actual (fallback a `freemium`).
- Cualquier cambio en catálogo de tiers o modelo de cuotas requiere actualización del contrato y, si es irreversible (p. ej., modelo de cobro), un ADR dedicado.
