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

## HISTORIAL_PR obligatorio
- Cambios en `docs/CONTRATO_*`, `docs/MUNAY_*`, `docs/02_ESTADO_Y_NORTE.md` o `docs/adr/*` requieren una nueva entrada en `docs/HISTORIAL_PR.md`.

## Pruebas y cobertura mínimas
Todo cambio de código debe validar como mínimo:
- `pytest -q`
- `pytest --cov=src --cov-fail-under=80`

## Prohibiciones
- Silenciar warnings o errores en CI o en código.
- Mezclar temas en una misma orden o PR.
- Cambiar contratos sin actualizar la documentación de ADRs y `docs/HISTORIAL_PR.md`.
