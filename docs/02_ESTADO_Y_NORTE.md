# NORTE MUNAY v2.1 — Estado y Principios Operativos

## 1. Principio Supremo
El proyecto Munay/SenseiKaizen debe avanzar sin contradicciones, sin retrocesos, sin redefinir decisiones previamente aprobadas.  
Toda modificación debe pasar por una **ORDEN KAIZEN** (L1, L2 o L3).

## 2. Gobernanza del Proyecto
El proyecto sigue un modelo **Contracts-First**, con la siguiente secuencia OBLIGATORIA:

1. Actualizar los contratos en `/docs/`
2. Actualizar historial PR
3. Alinear ADRs si aplica
4. recién después tocar código

Los contratos NO se ignoran, NO se contradicen, NO se redefinen sin orden formal.

### 2.1 Gobernanza SKB y ADRs
- `docs/CONTRATO_SKB_GOBERNANZA.md` es contrato fuente para prompts y órdenes (D→D→C, bloqueos y reglas contracts-first).
- `docs/CONTRATO_NEUTRO_CONTRIBUCION.md` es guía obligatoria para cualquier PR.
- `docs/adr/` contiene los ADRs obligatorios para cambios de arquitectura, seguridad o SLO/SLA; toda decisión usa `ADR_TEMPLATE.md`.
- Pipeline mínimo de CI (no negociable):
  - `.github/workflows/validate_norte.yml`
  - `.github/workflows/ci_tests.yml` (ejecuta `pytest -q` y `pytest --cov=src --cov-fail-under=80`).

---

## 3. SLOs oficiales (audio)
| Métrica | Valor |
|--------|--------|
| **audio_p95_ms** | ≤ 1500 ms |
| **error_rate_max** | ≤ 1% |
| **uptime_target** | 99.9% |
| **budget_burn_alert** | 85/90/95% |

Ver `docs/NEUTRO_SLO_AUDIO_OPERACIONAL.md` para la definición operativa, queries y alertas de referencia del SLO de audio.

Todas las implementaciones deben acercarse a estos límites incluso en pruebas.

---

## 4. UI como contrato
Toda respuesta debe incluir estos headers:

- `X-Outcome`
- `X-Correlation-Id`
- `X-Outcome-Detail` cuando aplica

El sistema debe mantener consistencia absoluta.

---

## 5. Observabilidad
Cada PR debe incluir:

- Métricas Prometheus necesarias  
- Queries PromQL  
- Alertas burn-rate  
- Umbrales alineados al SLO  
- Pruebas (k6 o equivalente)  

---

## 6. Flujo Kaizen (órdenes)

### **L1 — Agregar o corregir archivos de gobierno**
Contratos, NORTE, ADR, CI, runbooks.

### **L2 — Cambios en lógica, endpoints, modelos**
Implementación respetando contratos.

### **L3 — Refactors internos**
Sin cambiar comportamiento observable.

---

## 7. Regla de Coherencia entre Hilos
Cada nuevo hilo debe comenzar con este mensaje:

> Usa SIEMPRE los archivos del repo como verdad absoluta:  
> - `docs/02_ESTADO_Y_NORTE.md`  
> - `docs/HISTORIAL_PR.md`  
> - Todos los contratos NEUTRO  
> - Todos los contratos MUNAY  
> No redefines nada fuera de estos documentos.  
> Todo cambio requiere una ORDEN KAIZEN.

---

## 8. Estado Actual del Sistema (última actualización)
- Pipeline de audio completo con almacenamiento en memoria
- Pipeline de audio con providers enchufables (stub por defecto, Azure seleccionable por ENV)
- Azure Speech STT/TTS real disponible como opt-in local, con fallback automático a stub ante fallos
- Headers Munay (`x-munay-user-id`, `x-munay-context`) integrados
- Métricas runtime (`METRICS`) activas
- Rate-limit funcional por API key
- 100% de pruebas unitarias verdes  
- PRs recientes documentados en `HISTORIAL_PR.md`  

---

## 9. Filosofía del Proyecto
- **Máxima claridad**  
- **Cero contradicciones**  
- **Iteración sin pérdidas de coherencia**  
- La IA actúa como arquitecto, no como creativo descontrolado  
- Cada avance debe poder reproducirse sin error

---

## 10. Mantenimiento
Toda evolución del proyecto DEBE modificar este archivo.

