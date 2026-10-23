# 0005 — Documentação em docs/ como fonte de contexto

**Status:** aceito · **Data:** 2026-10-23

## Contexto
O desenvolvimento usa ferramentas de IA generativa (Claude Code, Codex, Gemini, Copilot). Reconstruir contexto a partir de conversas longas gasta tempo e tokens e gera divergência entre sessões.

## Decisão
- `docs/` é a fonte da verdade, organizada em arquivos pequenos por assunto, com índice em `docs/README.md`.
- `AGENTS.md` é o arquivo canônico de regras para agentes; `CLAUDE.md` o importa.
- Agentes buscam contexto nos `.md`, lendo só o necessário, e não no histórico de conversa.
- Decisões de conversa só valem quando registradas em ADR ou no `.md` do módulo; mudanças atualizam a documentação no mesmo commit.

## Consequências
- Sessões novas (de qualquer ferramenta) começam com contexto correto e barato.
- Disciplina de manutenção da documentação passa a fazer parte da definição de pronto.
