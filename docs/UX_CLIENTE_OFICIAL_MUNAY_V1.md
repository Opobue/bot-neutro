# UX_CLIENTE_OFICIAL_MUNAY_V1 – Dashboard mínimo para `/audio`

## 1. Objetivo UX

- Permitir que cualquier persona, sin conocer el backend, pueda:
  - Subir o grabar un audio rápidamente.
  - Ver de forma clara la transcripción y la respuesta generada.
  - Entender si está interactuando con el modelo real o con el stub.

## 2. Wireframes textuales

### Pantalla única (dashboard mínimo)

- **Header**: "Bot Neutro – Cliente Oficial Munay".
- **Sección Entrada**:
  - Botón "Subir audio" y opción "Grabar audio" (uno de los dos es suficiente si solo se implementa upload en la primera iteración).
  - Tooltip o texto breve indicando formato recomendado (wav, mono 16 kHz).
- **Sección Opciones**:
  - Selector de tier (toggle/combo): `freemium` (default) / `premium`.
  - Campo de configuración (oculto o modal) para API base y API key.
- **Sección Resultado**:
  - Bloque de `transcript` (texto grande, multilinea).
  - Bloque de `reply_text` (separado visualmente del transcript).
  - Métricas clave: `total_ms`, `provider_llm`, `corr_id`.
  - Etiqueta sutil "Modo stub activo" cuando `provider_llm` indique stub.
- **Estado de carga**: overlay o spinner deshabilitando acciones mientras se envía.

## 3. Casos de uso

1. **Prueba rápida freemium**
   - Usuario deja tier en `freemium`, sube audio corto, ve transcript + reply en segundos.

2. **Prueba premium**
   - Usuario selecciona `premium`, envía audio y valida que `provider_llm` refleje el proveedor premium.

3. **Error por API key incorrecta**
   - Con API key inválida, al enviar muestra error 401: "API Key inválida o ausente".

4. **Modo stub por falta de crédito**
   - Backend responde con `provider_llm` que contiene `stub`; UI muestra alerta/label "Modo stub activo (respuesta de prueba)" pero mantiene UX normal.
