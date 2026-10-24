# Transcritor Musical

Transcrição de gravações de orquestra e música de câmara para partitura editável, com editor assistido e áudio sincronizado.

Estado: F0 concluída (fundação: `core` com Score IR e `eval`); curadoria do conjunto mono-v1 em andamento.

## Começando

```
uv sync --all-packages
```

Portão de qualidade (o mesmo da CI):

```
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
uv run python scripts/check_licenses.py
```

Eval (ver `docs/modulos/eval.md`):

```
uv run transcritor-eval run --manifest packages/eval/datasets/ci/manifest.json --subset ci --pipeline null --out eval-out
uv run transcritor-eval gate --report eval-out/report.json --baseline packages/eval/baselines/ci.json
```

## Documentação

- Visão do produto: `docs/produto/visao.md`
- Índice da documentação: `docs/README.md`
- Regras para quem contribui (humanos e agentes de IA): `AGENTS.md`
