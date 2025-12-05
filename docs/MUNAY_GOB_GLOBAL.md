# MUNAY_GOB_GLOBAL

## Propósito
Establecer un germen de gobernanza global aplicable a todas las repos y servicios Munay (apps, bots, backends, dashboards). Este documento actúa como capa superior de principios innegociables que cada repo debe adoptar y adaptar mediante contratos locales y ADRs.

## Principios globales innegociables
- Contracts-first: decisiones documentadas en contratos (`docs/CONTRATO_*` locales), luego HISTORIAL_PR, después ADRs y finalmente código.
- Protocolo D→D→C obligatorio: toda entrega pasa por DESCUBRIR → DECIDIR → CAMBIAR, con BLOQUEO explícito cuando aplique.
- CI obligatorio con pruebas y cobertura mínima acordada por producto; no se aceptan merges con CI en rojo.
- No mezclar temas en una misma orden o PR; cada cambio debe tener intención única y trazable.
- Uso de un historial vivo (HISTORIAL_PR o equivalente) que registre órdenes/contratos aplicados antes de modificar código.
- SLOs y observabilidad mínima declarados por producto y validados continuamente; la ausencia de señales es un bloqueo.
- Seguridad y cumplimiento como primera clase: manejo de secretos, permisos y dependencias auditables.

## Relación con esta repo (Bot Neutro)
- Esta repo adhiere a `MUNAY_GOB_GLOBAL.md` como capa superior de principios.
- La gobernanza local se especifica en `docs/CONTRATO_SKB_GOBERNANZA.md` y en `docs/02_ESTADO_Y_NORTE.md`, que concretan cómo aplicar estos principios en Bot Neutro.
- En caso de conflicto, el principio global se respeta y se documenta la adaptación local vía contrato o ADR.

## Extensión futura
- Incluir lineamientos específicos para otras repos Munay (app móvil, dashboards, data pipelines) conforme se creen.
- Definir criterios formales de cumplimiento Munay (checklist mínima, CI requerida, SLOs por dominio).
- Documentar interoperabilidad entre repos (contratos compartidos, versiones, compatibilidad).
