#!/usr/bin/env python3
import re
import sys
from pathlib import Path

REQUIRED_HEADERS = [
    "## Metadata (obligatoria)",
    "## Objetivo de esta orden:",
    "## Alcance / Fuera de alcance:",
    "## Parches (DIFF) — obligatorios",
    "## DoD (Definition of Done) — obligatorio",
    "## Comandos de verificación — obligatorio",
    "## CI",
    "## Riesgos y mitigaciones",
    "## NO IMPLEMENTADO (y por qué)",
]

ALLOWED_TIPOS = {"DESCUBRIR", "DECIDIR", "CAMBIAR", "BLOQUEO"}
ALLOWED_NIVELES = {"L1", "L2", "L3"}


def _extract_kv(text: str, key: str) -> str | None:
    # Busca líneas tipo: KEY = valor
    match = re.search(rf"^{re.escape(key)}\s*=\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered == ""
        or lowered in {"...", "n/a", "na", "none"}
        or lowered.startswith("(")
        or "copiar" in lowered
        or "placeholder" in lowered
    )


def validate_order_text(text: str) -> list[str]:
    errors: list[str] = []

    missing_sections = [header for header in REQUIRED_HEADERS if header not in text]
    if missing_sections:
        errors.append("missing_sections:" + ",".join(missing_sections))
        return errors

    norte = _extract_kv(text, "NORTE_VERSION_ACTUAL")
    nivel = _extract_kv(text, "Nivel")
    tipo = _extract_kv(text, "TIPO")
    basado = _extract_kv(text, "Basado en")
    objetivo_operativo = _extract_kv(text, "Objetivo operativo")
    contratos = _extract_kv(text, "Contratos impactados")

    if norte is None or _is_placeholder(norte):
        errors.append("metadata:NORTE_VERSION_ACTUAL invalid/placeholder")
    if nivel is None or nivel not in ALLOWED_NIVELES:
        errors.append("metadata:Nivel invalid (expected L1|L2|L3)")
    if tipo is None or tipo not in ALLOWED_TIPOS:
        errors.append("metadata:TIPO invalid (expected DESCUBRIR|DECIDIR|CAMBIAR|BLOQUEO)")
    if basado is None or _is_placeholder(basado):
        errors.append("metadata:Basado en invalid/placeholder")
    if objetivo_operativo is None or _is_placeholder(objetivo_operativo):
        errors.append("metadata:Objetivo operativo invalid/placeholder")
    if contratos is None or _is_placeholder(contratos):
        errors.append("metadata:Contratos impactados invalid/placeholder")

    has_diff = "diff --git " in text
    if tipo == "CAMBIAR" and not has_diff:
        errors.append("rule:TIPO=CAMBIAR requires at least one 'diff --git' block")

    has_pytest = "pytest -q" in text
    has_cov = "--cov=src" in text and "--cov-fail-under=80" in text
    if not has_pytest:
        errors.append("rule:missing 'pytest -q' in verification commands")
    if not has_cov:
        errors.append("rule:missing coverage command '--cov=src --cov-fail-under=80'")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: kaizen_validate_order.py <path_to_order.md>")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"FAIL: file not found: {path}")
        return 2

    text = path.read_text(encoding="utf-8")
    errors = validate_order_text(text)
    if errors:
        print("FAIL: kaizen order validation errors:")
        for error in errors:
            if error.startswith("missing_sections:"):
                sections = error.split(":", 1)[1].split(",")
                print(" - missing sections:")
                for section in sections:
                    print(f"   - {section}")
            else:
                print(f" - {error}")
        return 1

    print("OK: kaizen order validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
