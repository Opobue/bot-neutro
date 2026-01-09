# RUBRICA_D1 (DESCUBRIR)

## Encabezado obligatorio
Primera línea no vacía:
```
TIPO=DESCUBRIR · OBJ=<texto> · ALCANCE=<texto>
```

## Secciones obligatorias (en este orden)
1) `## 1. CONTEXTO Y ALCANCE`
2) `## 2. HALLAZGOS (HECHOS)`
3) `## 3. INCERTIDUMBRES Y PREGUNTAS`
4) `## 4. RIESGOS Y OPORTUNIDADES (PRELIMINAR)`
5) `## 5. GATE D1→D2`

## Reglas de evidencia
- Cada línea que empiece con `HECHO:` debe contener evidencia verificable.
- Formatos válidos:
  - `(EVIDENCIA: path:Lx-Ly)`
  - `(EVIDENCIA: path#SHA256:<hash>)`

## Gate D1→D2 (contenido obligatorio)
Dentro de `## 5. GATE D1→D2` deben existir estos bloques:
- `### TOP 3 Bloqueos`
- `### TOP 3 Riesgos Antigravity`
- `### TOP 3 Oportunidades`
- `### Siguiente Acción Recomendada`
- `### Listo para D2`

Reglas del Gate:
- Cada TOP 3 debe listar al menos 3 ítems.
- Cada ítem en “TOP 3 Oportunidades” debe iniciar con una etiqueta:
  `[HECHO]`, `[INFERENCIA]`, `[HIPÓTESIS]`, `[DESCONOCIDO]`.
- La sección “Listo para D2” debe incluir la línea:
  `Listo para D2: Sí/No — <razón>`

## Prohibiciones (fallo automático)
- “Ninguno probado” en el Gate.
- “Sin evidencia” en cualquier sección.
