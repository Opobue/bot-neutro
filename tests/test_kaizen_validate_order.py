import subprocess
import sys
from textwrap import dedent



def _run_validator(path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/kaizen_validate_order.py", path],
        capture_output=True,
        text=True,
    )


BASE_OK = dedent(
    """
    # ORDEN DE EJECUCIÓN KAIZEN

    ## Regla de transparencia (obligatoria)
    - Todo lo recomendado debe quedar como: IMPLEMENTADO o NO IMPLEMENTADO.

    ## Metadata (obligatoria)
    NORTE_VERSION_ACTUAL = v2.1
    Nivel = L2
    TIPO = CAMBIAR
    Basado en = PR-123 (2025-12-17)
    Objetivo operativo = Validación real de órdenes
    Contratos impactados = docs/PLANTILLA_ORDEN_EJECUCION_KAIZEN.md

    ## Objetivo de esta orden:
    (una línea)

    ## Alcance / Fuera de alcance:
    - IN:
    - OUT:

    ## Parches (DIFF) — obligatorios
    diff --git a/x b/x

    ## DoD (Definition of Done) — obligatorio
    - [ ] tests pasan

    ## Comandos de verificación — obligatorio
    - pytest -q
    - pytest --cov=src --cov-fail-under=80

    ## CI
    [CI_REAL] (si aplica)

    ## Riesgos y mitigaciones
    - Riesgo:
    - Mitigación:

    ## NO IMPLEMENTADO (y por qué)
    - Item:
    - Por qué:
    """
).lstrip()


def test_validator_ok_for_cambiar_with_diff(tmp_path):
    path = tmp_path / "order.md"
    path.write_text(BASE_OK, encoding="utf-8")
    result = _run_validator(str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_validator_fails_when_file_missing(tmp_path):
    result = _run_validator(str(tmp_path / "nope.md"))
    assert result.returncode == 2


def test_validator_requires_diff_only_for_cambiar(tmp_path):
    text = BASE_OK.replace("diff --git a/x b/x", "")
    path = tmp_path / "order.md"
    path.write_text(text, encoding="utf-8")
    result = _run_validator(str(path))
    assert result.returncode == 1
    assert "TIPO=CAMBIAR requires" in (result.stdout + result.stderr)

    text_descubrir = text.replace("TIPO = CAMBIAR", "TIPO = DESCUBRIR")
    path2 = tmp_path / "order2.md"
    path2.write_text(text_descubrir, encoding="utf-8")
    result2 = _run_validator(str(path2))
    assert result2.returncode == 0, result2.stdout + result2.stderr


def test_validator_blocks_placeholder_metadata(tmp_path):
    bad = BASE_OK.replace(
        "NORTE_VERSION_ACTUAL = v2.1", "NORTE_VERSION_ACTUAL = (copiar exacto...)"
    )
    path = tmp_path / "order.md"
    path.write_text(bad, encoding="utf-8")
    result = _run_validator(str(path))
    assert result.returncode == 1
    assert "NORTE_VERSION_ACTUAL invalid/placeholder" in (result.stdout + result.stderr)


def test_validator_requires_min_commands(tmp_path):
    bad = BASE_OK.replace("- pytest -q", "- python -V")
    path = tmp_path / "order.md"
    path.write_text(bad, encoding="utf-8")
    result = _run_validator(str(path))
    assert result.returncode == 1
    out = result.stdout + result.stderr
    assert "missing 'pytest -q'" in out


def test_validator_requires_cov_command(tmp_path):
    bad = BASE_OK.replace(
        "- pytest --cov=src --cov-fail-under=80", "- pytest --cov=src"
    )
    path = tmp_path / "order.md"
    path.write_text(bad, encoding="utf-8")
    result = _run_validator(str(path))
    assert result.returncode == 1
    assert "missing coverage command" in (result.stdout + result.stderr)
