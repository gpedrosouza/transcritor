# Stack e layout do repositório

Contém: linguagens, ferramentas, estrutura de pastas, CI.

## Backend e pipeline

- Python 3.12, gerenciado com `uv` (workspace com um pacote por módulo).
- Pydantic v2 para a Score IR.
- `ruff` (lint e format), `mypy --strict` nos pacotes de domínio, `pytest`.
- FastAPI para o `service`; jobs em fila simples (SQLite + worker) até haver carga que justifique Redis/Postgres.
- Áudio: `soundfile`, `ffmpeg` (subprocesso) para decodificar formatos.

## Editor

- TypeScript + React + Vite.
- Verovio (WASM) para renderizar MusicXML/MEI no navegador.
- Web Audio API para reprodução sincronizada.
- Tipos da Score IR gerados do JSON Schema (`json-schema-to-typescript`).

## Ferramentas externas

- MuseScore 4 (CLI `mscore`), somente no servidor, para PDF. Ver licenças.

## Layout

```
transcritor/
├─ AGENTS.md, CLAUDE.md, README.md
├─ docs/                      # fonte da verdade (ver docs/README.md)
├─ packages/                  # Python (uv workspace)
│  ├─ core/                   # transcritor_core
│  ├─ ingest/
│  ├─ listen/
│  ├─ rhythm/
│  ├─ notate/
│  ├─ export/
│  ├─ flywheel/
│  └─ eval/
├─ apps/
│  ├─ service/                # FastAPI
│  ├─ cli/                    # `transcritor` CLI (F1)
│  └─ editor/                 # React
├─ data/                      # fora do git: áudio de teste, caches (ver eval)
└─ .github/workflows/         # CI
```

Cada pacote Python segue `packages/<m>/src/transcritor_<m>/` (código) e `packages/<m>/tests/` (testes). Scripts de repositório em `scripts/` (ex.: `check_licenses.py`). Nome de import: `transcritor_<modulo>` (ex.: `transcritor_notate`).

Eval: conjuntos em `packages/eval/datasets/<nome>/`, linhas de base em `packages/eval/baselines/<subset>.json`, áudio real em `data/eval/audio/` (fora do git). JSON Schema do ScoreDoc em `packages/core/schema/scoredoc.schema.json`.

## CI (a partir da F0)

Workflow `.github/workflows/ci.yml`, em cada push e PR:

1. `uv sync --all-packages --locked` (instala exatamente o que está no lockfile).
2. `ruff check`, `ruff format --check`, `mypy`.
3. `pytest` (unitários e golden files).
4. `python scripts/check_licenses.py` (ver `licencas.md`).
5. `transcritor-eval run` sobre o subconjunto `ci` com o pipeline nulo.
6. `transcritor-eval gate` comparando o relatório com `packages/eval/baselines/ci.json`.

O workflow roda com permissão de leitura apenas (`permissions: contents: read`).
