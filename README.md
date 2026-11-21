# Transcritor Musical

[![ci](https://github.com/gpedrosouza/transcritor/actions/workflows/ci.yml/badge.svg)](https://github.com/gpedrosouza/transcritor/actions/workflows/ci.yml)

> **EN —** Audio-to-score transcription for orchestral and chamber recordings: from a mixed recording to an editable score, one staff per instrument, with an assisted editor synced to the audio. The architecture is notation-first: audio models are pluggable adapters behind a single typed contract, the *Score IR*, and every model change has to pass an evaluation gate before it ships. **Status:** phase F0 (foundation) is done — Score IR + JSON Schema, evaluation harness and CI. The monophonic end-to-end pipeline (F1) is next.

Transcrição de gravações de orquestra e música de câmara para **partitura editável**: separar os instrumentos de uma faixa e escrever cada linha melódica, com um editor assistido e o áudio sincronizado.

## Princípios de arquitetura

- **Notação primeiro, áudio plugável.** O núcleo é o modelo de partitura e o motor de notação. Modelos de áudio (pitch, separação de fontes) são adaptadores atrás de interfaces e podem ser trocados sem tocar no resto ([ADR 0001](docs/decisoes/0001-notacao-primeiro-audio-plugavel.md)).
- **Um único contrato entre módulos.** A *Score IR* é tipada em Python, publicada como JSON Schema versionado ([`scoredoc.schema.json`](packages/core/schema/scoredoc.schema.json)) e usada para gerar os tipos do editor. Nenhum módulo troca dados em formato próprio.
- **Eval antes de otimizar.** Mudanças em `listen`, `rhythm` ou `notate` rodam o eval, e um *gate* compara as métricas de notas e de notação com a linha de base. Piorar além da tolerância bloqueia o merge.
- **Licenças verificadas na CI.** Pesos não comerciais (CC BY-NC) e AGPL são barrados por um script, porque o produto é comercial.
- **Avisar em vez de falhar.** Incerteza vira `warning` dentro do documento. Só erro real aborta.

## Roadmap

| Fase | Entrega | Estado |
|---|---|---|
| F0 | Fundação: Score IR, eval, CI | ✅ código concluído |
| F1 | Monofônico ponta a ponta: CLI → MusicXML + PDF | próxima |
| F2 | Editor assistido + flywheel de correções | — |
| F3 | API pública | — |
| F4 | Polifonia de um instrumento (piano, harpa) | — |
| F5 | Multi-instrumento (separação de fontes) | exploratório |
| F6 | Modelo próprio | pesquisa |

O detalhe de cada fase, com escopo e critério de saída medido no eval, está em [`docs/roadmap/fases.md`](docs/roadmap/fases.md).

## Estrutura

```
packages/core   Score IR (modelos, unidades racionais, instrumentos, schema, I/O)
packages/eval   alinhamento, métricas de notas e notação, runner, relatório, gate
docs/           produto, arquitetura, módulos, ADRs, specs, planos, pesquisa
```

Stack: Python 3.12 · uv workspace · Pydantic · ruff · mypy `--strict` · pytest · GitHub Actions

## Começando

```bash
uv sync --all-packages
```

Portão de qualidade (o mesmo da CI):

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
uv run python scripts/check_licenses.py
```

Eval com o pipeline nulo (ver [`docs/modulos/eval.md`](docs/modulos/eval.md)):

```bash
uv run transcritor-eval run --manifest packages/eval/datasets/ci/manifest.json --subset ci --pipeline null --out eval-out
uv run transcritor-eval gate --report eval-out/report.json --baseline packages/eval/baselines/ci.json
```

## Documentação e fluxo com IA

- Visão do produto: [`docs/produto/visao.md`](docs/produto/visao.md) · Índice: [`docs/README.md`](docs/README.md)
- [`AGENTS.md`](AGENTS.md) traz as regras para quem contribui, sejam humanos ou agentes de IA (Claude Code, Codex, Gemini). Todo contexto vem dos `.md` em `docs/`, e toda decisão vira ADR.
- O trabalho de porte segue *brainstorming → spec → plano → execução com TDD*.

## Autor

Guilherme Oliveira · [github.com/gpedrosouza](https://github.com/gpedrosouza)
