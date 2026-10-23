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

Nome de import Python: `transcritor_<modulo>` (ex.: `transcritor_notate`).

## CI (a partir da F0)

1. `ruff check`, `ruff format --check`, `mypy`.
2. `pytest` (unitários e golden files).
3. Checagem de licenças (ver `licencas.md`).
4. Eval rápido sobre o subconjunto de CI, comparando com a linha de base (a partir da F1).
