# CONTRATO_INFRAESTRUCTURA_GITHUB

Define los checks obligatorios para proteger la integridad de Munay.

1. CI-Validation (workflow: `CI Tests` / job: `CI-Validation`): Debe incluir Ruff, Mypy y Pytest (Cov >= 80%).
2. validate-norte (workflow: `Validate NORTE and PR history` / job: `validate-norte`): Debe verificar la sincronización de HISTORIAL_PR.
3. LLM Governance (D1) (workflow: `LLM Governance (D1)` / job: `LLM-Governance`): Debe validar el EvidencePack derivado del RepoPack generado en CI (ruta `/tmp`).

Cualquier cambio en estos nombres requiere un ADR.
