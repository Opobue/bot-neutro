# BOOTSTRAP_SKB_HILO

## Propósito
Este archivo define el mensaje semilla canónico que se debe pegar como primer mensaje en cualquier hilo nuevo donde SKB interactúe con el repositorio **Opobue/bot-neutro**. El objetivo es forzar arranques consistentes en modo memoria cero, utilizando la repo como única fuente de verdad.

## Mensaje semilla para hilos nuevos
Pega el siguiente bloque como primer mensaje. SKB debe ejecutarlo literalmente.

```
Repositorio: Opobue/bot-neutro
Fuente de verdad: docs/02_ESTADO_Y_NORTE.md, docs/HISTORIAL_PR.md, contratos docs/CONTRATO_* y docs/MUNAY_*, ADRs en docs/adr/
Instrucciones para SKB:
1) Lee completo el NORTE (docs/02_ESTADO_Y_NORTE.md).
2) Lee completo el HISTORIAL_PR (docs/HISTORIAL_PR.md). La última entrada es la última orden aplicada.
3) Responde primero con TIPO=DESCUBRIR. Debe incluir diagnóstico del estado actual y propuesta de siguiente ORDEN KAIZEN (L1/L2). No apliques cambios todavía.
```

## Protocolo de arranque de SKB (interno)
Cuando SKB reciba el mensaje anterior, debe:

1. Confirmar que el repositorio activo es **Opobue/bot-neutro**.
2. Leer `docs/02_ESTADO_Y_NORTE.md`, `docs/HISTORIAL_PR.md`, los contratos `docs/CONTRATO_*`, `docs/MUNAY_*` y ADRs disponibles.
3. Declarar explícitamente cuál es la última entrada de `docs/HISTORIAL_PR.md` y el alcance que habilita.
4. Mapear brevemente los contratos clave relevantes para el pedido inicial.
5. Emitir una respuesta TIPO=DESCUBRIR con diagnóstico y propuesta de siguiente ORDEN KAIZEN (L1 o L2). No ejecutar CAMBIAR hasta que el hilo tenga al menos una respuesta DESCUBRIR que cite NORTE + HISTORIAL.
6. Si cambia la gobernanza o el NORTE, reflejar los ajustes en este bootstrap y registrar el cambio en `docs/HISTORIAL_PR.md`.
