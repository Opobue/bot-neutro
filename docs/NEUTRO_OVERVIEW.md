# Bot Neutro: Overview

El **Bot Neutro** es la base común para bots como Munay y futuras variantes. Define contratos estables para API HTTP, audio, texto, acciones, observabilidad, headers, rate limit y el uso de LLMs sin imponer detalles de negocio. Este documento actúa como punto de entrada y referencia cruzada hacia los contratos específicos.

## Propósito
- Establecer un contrato homogéneo que mantenga compatibilidad con las pruebas actuales.
- Asegurar que cualquier bot derivado respete las mismas rutas, semántica de headers y expectativas de observabilidad.
- Servir como guía de referencia rápida para integradores y equipos que extienden el sistema.

## Componentes definidos
- **API HTTP neutra**: rutas base `/healthz`, `/readyz`, `/version`, `/metrics`, `/audio`, `/text`, `/actions` (según disponibilidad), con semántica y headers comunes.
- Los endpoints `/text` y `/actions` son opcionales: forman parte del contrato recomendado del Bot Neutro, pero una implementación mínima puede omitirlos siempre que preserve `/healthz`, `/readyz`, `/version`, `/metrics` y `/audio`.
- **Headers estándar**: trazabilidad (`X-Correlation-Id`) y estado (`X-Outcome`, `X-Outcome-Detail`).
- **Observabilidad**: endpoint `/metrics` con exportación Prometheus, métricas núcleo y SLOs orientativos.
- **Rate limit**: política de allowlist y semántica de respuestas 429.
- **Audio**: contrato de entrada/salida para `/audio` y su integración con métricas y usage.
- **LLM**: expectativas de latencia, manejo de errores y rol como "cerebro" agnóstico al proveedor.
- **Eventos lógicos**: trazabilidad mediante logs JSON y métricas.

## Reutilización para Munay y otros bots
- Los bots derivados deben reutilizar este contrato como baseline, preservando rutas, headers y comportamiento observable.
- Extensiones específicas (nuevos endpoints o acciones) pueden añadirse siempre que mantengan coherencia con observabilidad y rate limit.
- Las pruebas existentes sirven como red de seguridad para garantizar que el contrato neutro sigue vigente.

## Contratos relacionados
- [Contrato de API neutra](./CONTRATO_NEUTRO_API.md)
- [Contrato de headers](./CONTRATO_NEUTRO_HEADERS.md)
- [Contrato de observabilidad](./CONTRATO_NEUTRO_OBSERVABILIDAD.md)
- [Contrato de rate limit](./CONTRATO_NEUTRO_RATE_LIMIT.md)
- [Contrato de audio](./CONTRATO_NEUTRO_AUDIO.md)
- [Contrato de LLM](./CONTRATO_NEUTRO_LLM.md)
- [Contrato de eventos](./CONTRATO_NEUTRO_EVENTOS.md)

## Compatibilidad con tests actuales
- Mantiene la enumeración de endpoints (`/healthz`, `/readyz`, `/version`, `/metrics`, `/audio`) que ya son verificados por la suite.
- Conserva la semántica de headers y content-type descrita en los tests de observabilidad y rate limit.
- No requiere cambios en `src/`, asegurando que `pytest -q` y `pytest -k metrics -q` permanezcan en verde.

## Relación con código legacy

El repositorio actual aún contiene componentes legacy específicos del bot original (SenseiKaizen).
Estos módulos están inventariados en [LEGACY_SENSEI_MAP](./LEGACY_SENSEI_MAP.md) y etiquetados
en el código con el marcador `LEGACY_NEUTRO`. El contrato del Bot Neutro se define de forma
independiente para facilitar la futura extracción o eliminación de ese código legacy.
Para los detalles de cómo se migrará este código legacy y en qué fases,
ver [NEUTRO_MIGRATION_PLAN](./NEUTRO_MIGRATION_PLAN.md).
