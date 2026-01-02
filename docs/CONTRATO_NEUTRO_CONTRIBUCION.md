# CONTRATO_NEUTRO_CONTRIBUCION

Documento de referencia oficial para cualquier persona (humana o IA) que abra un Pull Request en este repositorio.

## Checklist previo a abrir un PR
1. El PR cita explícitamente el/los contrato(s) habilitante(s) en su descripción.
2. `docs/HISTORIAL_PR.md` está actualizado si se tocaron contratos o el NORTE.
3. `pytest -q` y `pytest --cov=src --cov-fail-under=80` se ejecutaron (local o CI) y están en verde.
4. El PR tiene **una sola intención**; no mezcla temas.
5. La descripción del PR incluye TIPO (DESCUBRIR/DECIDIR/CAMBIAR/BLOQUEO) y referencia a secciones de contrato/ADR relevantes.

6. Verificación de realidad del NORTE:
   [ ] La orden/PR cita NORTE_VERSION_ACTUAL exactamente como aparece en `docs/02_ESTADO_Y_NORTE.md`.
   [ ] No se mencionan secciones o versiones de NORTE que no existan.

7. CI REAL vs futuro:
   [ ] Los checks de CI en la orden/PR corresponden a workflows existentes en `.github/workflows`, salvo que esta misma orden los cree o modifique.

8. Limpieza de artefactos IA:
   [ ] El texto no contiene patrones tipo "contentReference[", "oaicite:", "<<ImageDisplayed>>" salvo que sean ejemplos explícitos.

## Bootstrap reproducible (Codex / agentes / dev local)

Objetivo: ejecutar exactamente lo mismo que CI (deps + comandos) y evitar fallos por `missing httpx` / `pytest-cov`.

### Comando único (deps + herramientas CI)
1. Crear y activar entorno virtual.
2. Instalar dependencias de test **solo** por la vía oficial:
   - Preferido (existe extra dev): `pip install -e ".[dev]"`
   - Alternativa (solo si existiera `requirements-dev.txt`): `pip install -r requirements-dev.txt`
3. El extra `.[dev]` incluye todo lo necesario para CI (incluyendo ruff/mypy si aplica).

Ejemplo Linux/macOS (una sola línea):
```bash
python -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && pip install -e ".[dev]"
```

En Windows usar el script `scripts/bootstrap_codex.ps1`.

### Verificación de paquetes críticos
```bash
python -m pip show httpx
python -m pip show pytest-cov
```

### Comandos CI (idénticos a CI)
```bash
pytest -q
pytest --cov=src --cov-fail-under=80
ruff check .
mypy src/
```
