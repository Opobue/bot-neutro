# Starter Kit del Bot Neutro

## Propósito del Starter Kit
- Define el **mínimo conjunto de archivos** necesario para clonar un bot en blanco alineado al contrato neutro.
- Sirve como base para bots como Munay u otros derivados que compartan la misma arquitectura HTTP y de observabilidad.
- Es 100% compatible con la suite actual (`pytest -q`, `pytest -k metrics -q`) sin requerir cambios en código.
- No fija proveedor de LLM ni STT/TTS; establece contratos y estructura para que cada implementación conecte sus propios proveedores.
- Facilita la trazabilidad estándar (headers, logs y métricas) sin imponer lógica de negocio específica.

## Conjunto mínimo de archivos (referencia)
Estos archivos ya existen en el repositorio y conforman la referencia de un Bot Neutro. No se modifican en esta orden; solo se listan para orientar clonados futuros.

- **Core API / HTTP**:
  - `src/sensei/api.py`
  - Rutas principales: `src/sensei/routes/audio.py`, y (si existen) `src/sensei/routes/text.py`, `src/sensei/routes/actions.py`.
- **Middleware y observabilidad**:
  - `src/sensei/middleware/log_json.py`
  - `src/sensei/middleware/observability.py`
  - `src/sensei/middleware/rate_limit.py`
  - `src/sensei/routers/metrics.py` o el módulo equivalente que expone `/metrics`.
- **Autenticación / API keys**:
  - `src/sensei/services/api_keys.py`
- **Providers / LLM / STT / TTS**:
  - `src/sensei/providers/factory.py`
- **Métricas y uso de audio**:
  - `src/sensei/metrics.py`
- **Configuración / settings**:
  - `src/sensei/settings.py`
- **Tests clave que protegen el contrato neutro**:
  - Tests de healthz/readyz/version.
  - Tests de `/metrics` (observabilidad, Prometheus).
  - Tests de rate limit.
  - Tests de `/audio`.

Importante: esta lista es de referencia y no implica mover ni modificar archivos en L3.

## Pasos conceptuales para clonar un Bot Neutro
1. Crear un nuevo repositorio vacío.
2. Copiar la estructura base de `src/sensei` necesaria (sin los módulos opcionales que no se requieran).
3. Copiar los contratos `docs/NEUTRO_OVERVIEW.md` y todos los `CONTRATO_NEUTRO_*.md`.
4. Ajustar el nombre del bot (p. ej., de `sensei` → `munay` en una fase posterior), manteniendo la estructura y los contratos intactos.
5. Preservar los endpoints `/healthz`, `/readyz`, `/version`, `/metrics`, `/audio` y los headers estándar; `/text` y `/actions` pueden omitirse si no se requieren en la versión mínima.

La implementación concreta del nuevo bot se realizará en una fase posterior (otra orden Kaizen), no en L3.

> Nota: en el repositorio actual, los componentes marcados como legacy están documentados
> en [LEGACY_SENSEI_MAP](./LEGACY_SENSEI_MAP.md). Al clonar un Bot Neutro, se recomienda
> incluir solo los módulos alineados al contrato neutro y dejar fuera el código marcado
> como `LEGACY_NEUTRO`, salvo que se necesite explícitamente.

## Relación con los contratos neutros
El starter kit está gobernado por los contratos existentes:
- `NEUTRO_OVERVIEW.md`
- `CONTRATO_NEUTRO_API.md`
- `CONTRATO_NEUTRO_HEADERS.md`
- `CONTRATO_NEUTRO_OBSERVABILIDAD.md`
- `CONTRATO_NEUTRO_RATE_LIMIT.md`
- `CONTRATO_NEUTRO_AUDIO.md`
- `CONTRATO_NEUTRO_LLM.md`
- `CONTRATO_NEUTRO_EVENTOS.md`

Cualquier bot derivado debe seguir estos contratos salvo extensiones explícitamente documentadas.

## Compatibilidad con la suite de tests actual
Este starter kit no introduce cambios en `src/` ni en la configuración actual de tests. Después de crear estos documentos, los comandos `pytest -q` y `pytest -k metrics -q` deben seguir pasando en verde sin modificaciones adicionales.
