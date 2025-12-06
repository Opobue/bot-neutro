# CONTRATO_SKB_GOBERNANZA

Este contrato convierte la gobernanza SKB en un requisito operativo para cualquier contribución (humana o IA) en este repositorio.

## Protocolo D→D→C (DESCUBRIR → DECIDIR → CAMBIAR)
- **DESCUBRIR (D1):** Identificar brechas, riesgos o necesidades. No se cambia nada.
- **DECIDIR (D2):** Seleccionar la solución o contrato habilitante. No se modifica código de negocio hasta formalizar la decisión.
- **CAMBIAR (C):** Ejecutar la implementación autorizada por contratos/ADRs.
- **BLOQUEO:** Si no es posible avanzar, se debe emitir bloqueos explícitos.

### Cabecera obligatoria en cada respuesta
```
TIPO={DESCUBRIR|DECIDIR|CAMBIAR|BLOQUEO} · OBJ={{1 frase}} · ALCANCE={{resumen corto}}
```

### Formato de BLOQUEO
```
BLOQUEO:{causa}·Evidencia:{arch:línea}·Propuesta/Sig.paso:{acción mínima}
```

## Contracts-First y ADRs
- Ningún cambio de código de negocio puede ocurrir sin citar contrato(s) habilitantes (ejemplo: `CONTRATO_NEUTRO_AUDIO_PIPELINE.md §Semántica`).
- Cualquier cambio de arquitectura, seguridad o SLO/SLA requiere un ADR en `docs/adr/` siguiendo `ADR_TEMPLATE.md`.
- Si cambian los comandos de pruebas/cobertura, esta sección debe actualizarse en el mismo PR y registrarse en `docs/HISTORIAL_PR.md`.

## Hilos nuevos y memoria cero
- En hilos nuevos, SKB debe asumir **memoria cero** y reconstruir el contexto exclusivamente desde el repositorio: `docs/02_ESTADO_Y_NORTE.md`, `docs/HISTORIAL_PR.md`, contratos `docs/CONTRATO_*`, contratos `docs/MUNAY_*` y ADRs.

## Protocolo de arranque obligatorio
- Antes de cualquier respuesta TIPO=CAMBIAR debe existir al menos una respuesta TIPO=DESCUBRIR en el hilo.
- Esa respuesta DESCUBRIR debe citar explícitamente el NORTE y el HISTORIAL, identificando cuál es la última entrada de `docs/HISTORIAL_PR.md` y el alcance que habilita.
- Está prohibido saltar directamente a CAMBIAR en hilos nuevos o sin haber acreditado lectura del NORTE + HISTORIAL.

### NORTE_version_no_inventada
- Cada ORDEN KAIZEN debe incluir el campo:
  - `NORTE_VERSION_ACTUAL = vX.Y` (copiado literalmente de la primera línea de `docs/02_ESTADO_Y_NORTE.md`).
- Si el valor declarado no coincide con el valor real del archivo, la orden es inválida y debió emitirse un BLOQUEO.

### CI_REAL vs CI_FUTURO
- `CI_REAL`: workflows existentes en `.github/workflows/**`.
- `CI_FUTURO`: checks deseados sin workflow implementado.
- Ninguna orden puede usar checks de `CI_FUTURO` como criterio obligatorio de Definition of Done, salvo que incluya en su alcance la creación o modificación de esos workflows.

### Niveles L1 / L2 / L3
- **L1:** cambios puros de gobernanza/contratos (NORTE, HISTORIAL, contratos, ADRs, plantillas). No tocan código de runtime ni tests. Ejemplo: ajustar `CONTRATO_SKB_GOBERNANZA.md` o actualizar `docs/PLANTILLA_ORDEN_EJECUCION_KAIZEN.md`.
- **L2:** cambios de funcionalidad que pueden tocar contratos y código, siempre sobre un único tema y actualizando el contrato habilitante en el mismo PR. Ejemplo: modificar `/audio` y actualizar el contrato correspondiente.
- **L3:** refactors internos sin cambios de contratos externos ni comportamiento observable (estructura o deuda técnica). Ejemplo: reorganizar módulos internos manteniendo firmas públicas.

### Referencia obligatoria al último DESCUBRIR
- Toda orden L2/L3 debe referenciar explícitamente la última respuesta TIPO=DESCUBRIR del hilo (fecha/hora o identificador) y declarar que no existen cambios en NORTE/HISTORIAL posteriores a ese diagnóstico.
- Si hay cambios en NORTE o HISTORIAL después del último DESCUBRIR, SKB debe emitir TIPO=BLOQUEO y solicitar un nuevo DESCUBRIR antes de aceptar la orden.

### Catálogo de artefactos de IA prohibidos
Las órdenes deben mantenerse libres de tokens de sistemas de IA ajenos. Patrones como los siguientes invalidan la orden y requieren corrección antes de un PR:
- `contentReference[`.
- `oaicite:`.
- `<<ImageDisplayed>>`.
- Cualquier otro token de sistema de IA que no sea parte explícita del diseño.

## Bloqueos automáticos
El siguiente catálogo de bloqueos es obligatorio. Cada bloqueo debe emitirse en formato `BLOQUEO:{causa}·Evidencia:{arch:línea}·Propuesta/Sig.paso:{acción mínima}`.

- `repo_inaccesible`: no se puede leer el repositorio. Ejemplo: `BLOQUEO:repo_inaccesible·Evidencia:git/clone·Propuesta/Sig.paso:reintentar o proveer acceso`.
- `norte_inexistente`: falta `docs/02_ESTADO_Y_NORTE.md`. Ejemplo: `BLOQUEO:norte_inexistente·Evidencia:docs/02_ESTADO_Y_NORTE.md·Propuesta/Sig.paso:crear/restaurar NORTE antes de continuar`.
- `historial_inexistente`: falta `docs/HISTORIAL_PR.md`. Ejemplo: `BLOQUEO:historial_inexistente·Evidencia:docs/HISTORIAL_PR.md·Propuesta/Sig.paso:crear historial para registrar órdenes`.
- `ci_rota_validate_norte`: el workflow `validate_norte.yml` falla de forma persistente en la rama `main`. Ejemplo: `BLOQUEO:ci_rota_validate_norte·Evidencia:.github/workflows/validate_norte.yml·Propuesta/Sig.paso:reparar validaciones del NORTE antes de nuevos cambios`.
- `ci_rota_tests`: el workflow `ci_tests.yml` falla de forma persistente en la rama `main`. Ejemplo: `BLOQUEO:ci_rota_tests·Evidencia:.github/workflows/ci_tests.yml·Propuesta/Sig.paso:corregir tests/cobertura antes de seguir`.

## HISTORIAL_PR obligatorio
- Cambios en `docs/CONTRATO_*`, `docs/MUNAY_*`, `docs/02_ESTADO_Y_NORTE.md` o `docs/adr/*` requieren una nueva entrada en `docs/HISTORIAL_PR.md`.

## Órdenes multi-tema
- Si una petición inicial mezcla múltiples temas (por ejemplo audio + rate-limit + UI), SKB debe responder con TIPO=BLOQUEO por mezcla de fases/alcances y proponer la partición en varias ORDEN KAIZEN atómicas.

## Pruebas y cobertura mínimas
Todo cambio de código debe validar como mínimo:
- `pytest -q`
- `pytest --cov=src --cov-fail-under=80`

## Prohibiciones
- Silenciar warnings o errores en CI o en código.
- Mezclar temas en una misma orden o PR.
- Cambiar contratos sin actualizar la documentación de ADRs y `docs/HISTORIAL_PR.md`.

## Relación con MUNAY_GOB_GLOBAL
Esta gobernanza SKB implementa localmente los principios globales definidos en `docs/MUNAY_GOB_GLOBAL.md`, adaptándolos a la operación de esta repo.
