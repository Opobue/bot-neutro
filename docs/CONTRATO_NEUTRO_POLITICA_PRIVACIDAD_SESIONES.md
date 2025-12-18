# CONTRATO_NEUTRO_POLITICA_PRIVACIDAD_SESIONES.md

## Alcance
- Aplica a la entidad `audio_session` definida en `docs/CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md` y a cualquier repositorio o endpoint que permita leerla o listarla.

## Control de acceso y multi-tenant
- Multi-tenant estricto: aislamiento por `api_key_id`/tenant; se prohíbe cualquier acceso cruzado entre tenants.
- Toda lectura requiere autenticación con `X-API-Key` válida.
- La lectura/listado de sesiones solo puede devolver datos cuando `api_key_id` solicitado == `api_key_id` autenticada.
- `list_by_user` únicamente puede entregar sesiones cuando `api_key_id` de la sesión coincide con la autenticada; colisiones de `user_external_id` entre tenants no generan error pero nunca revelan datos de otros tenants.

## Campos sensibles y minimización
- Se consideran sensibles: `transcript`, `reply_text`, `meta_tags`, `user_external_id`.
- Minimización: las vistas o dashboards agregados (métricas, estadísticas de uso, reportes sin granularidad de sesión) excluyen por defecto los campos sensibles listados arriba.

## Retención y purga obligatoria
- `retention_days` por defecto es 30; el campo `expires_at` es obligatorio en cada `audio_session`.
- Variables de configuración: `AUDIO_SESSION_RETENTION_DAYS` (días de retención, entero) y `AUDIO_SESSION_PURGE_ENABLED` (1/0 para habilitar la purga automática). Defaults seguros deben aplicarse si las variables no están definidas.
- La purga debe eliminar sesiones con `expires_at <= now`; las sesiones sin `expires_at` se consideran expiradas para evitar retención indefinida.

## Auditoría, logging y rate-limit de lecturas
- Registrar accesos de lectura (sin agregar PII adicional) cuando existan endpoints de lectura.
- Aplicar rate-limit de lecturas cuando existan endpoints de lectura para evitar scraping o abusos.

## Bloqueo y dependencias
- Está prohibido exponer endpoints o dashboards de lectura hasta cumplir esta política (sin excepciones salvo nueva Orden Kaizen).
- La política es de cumplimiento obligatorio y se referencia desde `CONTRATO_NEUTRO_STORAGE_SESIONES_AUDIO.md`.
