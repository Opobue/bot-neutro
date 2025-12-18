# DECISION_POLITICA_SESIONES_AUDIO_V1_20251217

- Decisión: no exponer endpoints de lectura hasta cumplir política.
- Decisión: retention default 30 días, configurable por env.
- Decisión: enforcement mínimo en storage in-memory (expires_at + purge + tenant isolation).
- Riesgo mitigado: fuga de PII entre tenants.
- Próxima orden sugerida: persistencia + endpoints seguros (L3), cuando se defina auth/roles y rate-limit de lecturas.
