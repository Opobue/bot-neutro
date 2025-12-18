#!/usr/bin/env python3
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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: kaizen_validate_order.py <path_to_order.md>")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"FAIL: file not found: {path}")
        return 2

    text = path.read_text(encoding="utf-8")

    missing = [header for header in REQUIRED_HEADERS if header not in text]
    has_diff = "diff --git " in text

    if missing:
        print("FAIL: missing sections:")
        for header in missing:
            print(f"- {header}")
        return 1

    if not has_diff:
        print("FAIL: order must include at least one 'diff --git' block")
        return 1

    print("OK: kaizen order validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
