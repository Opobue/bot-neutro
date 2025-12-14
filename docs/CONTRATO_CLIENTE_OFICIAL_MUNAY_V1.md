# CONTRATO_CLIENTE_OFICIAL_MUNAY_V1 – Dashboard web mínimo para `/audio`

## 1. Rol del cliente oficial

- Actúa como **referente oficial** de cómo consumir la API Pública v1 (`/audio`).
- Es el primer cliente oficial pensado para Munay y demos, sin atarse a una UI específica de la app móvil.
- Sirve como guía de implementación para otros clientes futuros que quieran replicar el consumo.

## 2. Flujo básico de una llamada

1. El usuario abre el dashboard web.
2. Selecciona o graba un archivo de audio local.
3. El dashboard:
   - Lee `X-API-Key` desde configuración (no debe aparecer hardcodeada en la UI).
   - Permite elegir `freemium` o `premium` como tier lógico (combo/toggle que alimenta `x-munay-llm-tier`).
   - Envía `POST /audio` con `multipart/form-data` incluyendo `audio_file` y los headers requeridos.
4. Recibe JSON con, al menos, `transcript`, `reply_text`, `usage.*` y `corr_id`.
5. Renderiza en pantalla:
   - Texto transcrito (`transcript`).
   - Respuesta del modelo (`reply_text`).
   - Métricas clave (`usage.total_ms`, `usage.provider_llm`).

## 3. Datos mínimos que el dashboard DEBE manejar

### Inputs

- `audio_file`: archivo subido o grabado por el usuario.
- Selector de tier: `freemium` (default) o `premium`.

### Headers

- `X-API-Key`: obtenido desde la configuración/env del frontend.
- `x-munay-llm-tier`: derivado de la selección de tier; default `freemium`.

### Outputs (renderizados en UI)

- `transcript`
- `reply_text`
- `usage.total_ms`
- `usage.provider_llm`
- `corr_id` (visible o accesible para debug/logs avanzados)

## 4. Estados de UI

- **Estado inicial**
  - Botón “Subir audio” o “Grabar audio”.
  - Campo de selección de tier (combo o toggle simple).
  - Zona vacía para resultados.

- **Estado “enviando”**
  - Indicador de carga y botones deshabilitados mientras se procesa.

- **Estado “OK” (200)**
  - Mostrar `transcript` en texto visible.
  - Mostrar `reply_text` en bloque separado.
  - Mostrar `usage.total_ms`, `usage.provider_llm`, `corr_id`.
  - Si `provider_llm` contiene `stub`, mostrar indicación sutil: “Modo stub activo (respuesta de prueba)”.

- **Estado de error 401**
  - Mensaje claro: “API Key inválida o ausente”.

- **Estado de error 422**
  - Mensaje: “Archivo de audio faltante o formato inválido”.

- **Errores de red / 5xx**
  - Mensaje genérico: “Error de servidor o red. Intenta de nuevo más tarde”.

## 5. Configuración esperada

- El dashboard debe poder configurarse mediante variables de entorno o archivo de config:
  - `API_BASE_URL` (por defecto `http://127.0.0.1:8000`).
  - `X-API-Key`.
  - Valor por defecto de tier (`freemium`).
- Evitar hardcodear la API key en el UI; usar configuración separada.

## 6. Observabilidad mínima desde el cliente

- El dashboard debe loguear (consola o panel) para cada llamada:
  - `corr_id`.
  - `usage.total_ms`.
  - `usage.provider_llm`.
- Estos datos deben estar disponibles para correlacionar con logs del backend.
