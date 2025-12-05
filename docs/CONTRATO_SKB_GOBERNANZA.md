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
