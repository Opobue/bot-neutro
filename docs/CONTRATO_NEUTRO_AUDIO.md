# Contrato Neutro de Audio (`/audio`)

Define la interacción de audio para el Bot Neutro, manteniendo neutralidad de proveedor.

## Entrada
- **Endpoint**: `POST /audio`
- **Formato**: `multipart/form-data`
- **Campo**: `file`
- **Tipos aceptados**: audio común (ej.: `audio/wav`, `audio/mpeg`); los tipos exactos dependen de validaciones actuales.
- **Header opcional**: `x-munay-llm-tier` para seleccionar modelo LLM (`freemium`/`premium`, case-insensitive). Valores ausentes o inválidos se tratan como `freemium`.

## Flujo de procesamiento
1. Recepción del archivo y validación básica de tipo/tamaño.
2. Transcripción (STT) a texto.
3. Procesamiento en el LLM con contexto disponible.
4. Generación de respuesta en texto y, si corresponde, síntesis TTS.
5. Respuesta JSON con transcript, texto final y referencia al audio TTS (url o bytes según implementación).

## Respuestas
- **200 OK**: incluye `transcript`, `reply_text` y `audio`/`audio_url` si aplica.
- **415 Unsupported Media Type**: tipo de archivo no soportado.
- **400/500**: errores de validación o internos. Se devuelven con `X-Outcome: error` y `X-Outcome-Detail` apropiado.

## Métricas y observabilidad
- La latencia del request se registra en `sensei_request_latency_seconds_bucket` con etiqueta de ruta `/audio`.
- Errores incrementan `errors_total`.
- Uso de audio puede registrarse vía `UsageMetrics` (segundos, proveedor, fallback) según contrato existente.

## Compatibilidad con tests actuales
- Mantiene el método `POST` y la forma `multipart/form-data` que verifican los tests de audio.
- La integración con métricas de latencia y contadores concuerda con las aserciones en `pytest -k metrics`.
- No altera validaciones ni proveedores, preservando el comportamiento esperado por la suite completa.
