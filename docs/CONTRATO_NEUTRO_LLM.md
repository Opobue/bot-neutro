# Contrato Neutro de LLM

Define el rol y expectativas del componente de lenguaje dentro del Bot Neutro, manteniendo independencia del proveedor.

## Rol en el pipeline
- **Input**: mensajes de usuario y contexto en texto plano (incluida la transcripción de audio cuando aplica).
- **Proceso**: generación de respuesta y posibles instrucciones para acciones externas.
- **Output**: texto final para el usuario y, opcionalmente, instrucciones estructuradas para `/actions`.

## Neutralidad de proveedor
- El contrato no fija proveedor (OpenAI, Azure, etc.); solo define la forma de entrada y salida.
- Las integraciones específicas deben respetar los headers y métricas del resto del sistema.

## Expectativas mínimas
- **Latencia**: alineada a los SLOs generales (p95 ≈ 1500 ms para audio incluye etapa LLM). Requests que excedan deben registrarse en métricas de latencia.
- **Errores**: se propagan como `X-Outcome=error` en la capa API y se registran en `errors_total`.
- **Trazabilidad**: uso de `X-Correlation-Id` para enlazar logs y métricas.

## Compatibilidad con tests actuales
- El manejo de errores y su registro en métricas concuerda con las aserciones de la suite de observabilidad.
- No modifica firmas de endpoints ni lógica de runtime, por lo que las pruebas de `/audio` y métricas permanecen válidas.
- La neutralidad de proveedor evita cambios en mocks o configuraciones verificadas por `pytest -q`.

## Contrato operativo neutral
- Interfaz propuesta: `generate_reply(transcript: str, context: dict) -> str`.
- Atributos esperados alineados a otros providers: `provider_id: str` y `latency_ms: int` (opcional pero recomendado para métricas homogéneas).
- El stub LLM debe ser determinista y libre de dependencias externas para que los tests base y coverage funcionen sin red ni SDKs.
- Integraciones reales (Azure OpenAI, OpenAI, SenseiKaizen/Munay) se habilitarán como opt-in, sin modificar el contrato ni exigir variables de entorno en CI.

## Selección de proveedor por entorno
- La variable `LLM_PROVIDER` define qué implementación concreta se usa:
  - `""`, `stub` o valor ausente → `StubLLMProvider` (modo determinista por defecto).
  - `openai` → `OpenAILLMProvider` con fallback al stub si hay errores.
  - Futuros proveedores: `azure_openai`, `local_llm`, etc., se agregarán sin romper el contrato.
- El contrato de interfaz **no cambia**: `generate_reply(transcript: str, context: dict) -> str`.

## Uso recomendado de `context`
- Clave sugerida: `context["llm_tier"]` ∈ {`"freemium"`, `"premium"`} para elegir el modelo dentro del provider.
- Si falta la clave, el provider debe asumir `"freemium"` (o su valor por defecto interno).
- El resto de metadata de negocio (usuario, tags, etc.) viaja en `context` pero no altera la firma.
