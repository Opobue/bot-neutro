# bot-neutro

## Descripción
bot-neutro es un núcleo contract-first basado en FastAPI que expone los endpoints:

- `GET /healthz`
- `GET /readyz`
- `GET /version`
- `GET /metrics`
- `POST /audio` (stub, responde 501 por ahora)

Este repositorio es la base neutra a partir de la cual se clonarán bots específicos (por ejemplo, Munay), respetando los contratos definidos en `docs/CONTRATO_NEUTRO_*.md`.

## Instalación local
```bash
git clone https://github.com/Opobue/bot-neutro.git
cd bot-neutro
python -m venv .venv
source .venv/bin/activate  # o .\.venv\Scripts\Activate.ps1 en Windows
pip install -e .[dev]
pytest -q
```

## Ejecución del servidor
```bash
uvicorn bot_neutro.api:app --reload --port 8001
```

Luego puedes probar en:

- http://localhost:8001/healthz
- http://localhost:8001/readyz
- http://localhost:8001/version
- http://localhost:8001/metrics

## Contratos Neutro
Los contratos y el diseño contract-first viven en `docs/CONTRATO_NEUTRO_*.md` y `docs/NEUTRO_OVERVIEW.md`. Este núcleo servirá como base para bots específicos como Munay.
