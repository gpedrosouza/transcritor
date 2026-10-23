# Índice da documentação

Leia só o que a tarefa exige. Cada arquivo diz no topo o que contém.

| Preciso de… | Arquivo |
|---|---|
| Por que o produto existe, para quem, o que é sucesso | `produto/visao.md` |
| Termos musicais e técnicos usados no projeto | `glossario.md` |
| Visão da arquitetura, módulos e fluxo | `arquitetura/visao-geral.md` |
| Contrato de dados entre módulos (ScoreDoc) | `arquitetura/score-ir.md` |
| Linguagens, ferramentas, layout do repositório | `arquitetura/stack.md` |
| O que pode e o que não pode ser usado (licenças) | `arquitetura/licencas.md` |
| Responsabilidade e interface de um módulo | `modulos/<modulo>.md` |
| Ordem de entrega e critérios de saída | `roadmap/fases.md` |
| Por que algo foi decidido | `decisoes/NNNN-*.md` |
| Spec detalhada de uma fase | `specs/` (criada por fase) |
| Plano de implementação de uma fase | `planos/` (criado por fase) |
| Estado da arte de modelos e ferramentas (10/2026) | `pesquisa/estado-da-arte-2026-10.md` |

## Módulos

`core` · `ingest` · `listen` · `rhythm` · `notate` · `export` · `service` · `editor` · `flywheel` · `eval` · futuros: `separate`, `train` (em `modulos/futuros.md`)

## Regra de manutenção

Toda mudança de contrato, comportamento ou decisão atualiza o arquivo correspondente no mesmo commit. Decisões novas viram um ADR em `decisoes/` e nunca editam um ADR antigo.
