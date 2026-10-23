# AGENTS.md — Transcritor Musical

Instruções para qualquer agente de IA (Claude Code, Codex, Gemini, Copilot) e para humanos que trabalhem neste repositório. Leia este arquivo inteiro antes de agir.

## 1. O que é o projeto

Produto comercial que transcreve gravações de orquestra e música de câmara em partitura editável. A primeira forma de entrega é um editor assistido, com o áudio sincronizado à partitura. A API pública vem depois. Visão completa: `docs/produto/visao.md`.

## 2. Regra de contexto: a documentação é a fonte da verdade

- **Todo contexto vem dos arquivos `.md` em `docs/`, não do histórico de conversa.** Comece sempre por `docs/README.md` (índice) e leia **só** os arquivos que a tarefa exige. Não leia a pasta inteira.
- Uma decisão tomada em conversa **não existe** até ser registrada em `docs/decisoes/` (ADR) ou no `.md` do módulo afetado.
- Se a documentação contradiz o código, ou se algo não está documentado, **pare e pergunte**. Não invente premissas.
- Ao concluir uma mudança que altere contrato, comportamento ou decisão, **atualize o `.md` correspondente no mesmo commit**.
- `docs/pesquisa/` é referência histórica (estado da arte em 10/2026). Consulte só quando a tarefa envolver escolha de modelo ou biblioteca.

## 3. Premissas inegociáveis

1. **Notação primeiro, áudio plugável.** O núcleo é o modelo de partitura e o motor de notação. Modelos de áudio são adaptadores atrás de interfaces (ADR 0001).
2. **Score IR é o único contrato entre módulos.** Nenhum módulo troca dados em formato próprio. Ver `docs/arquitetura/score-ir.md` (ADR 0003).
3. **Licenças.** Só entram dependências e pesos de modelo permitidos por `docs/arquitetura/licencas.md`. Pesos não comerciais (CC BY-NC) e AGPL são proibidos. Na dúvida, não adicione e pergunte (ADR 0002).
4. **Eval antes de otimizar.** Mudança em `listen`, `rhythm` ou `notate` precisa rodar o eval e não pode piorar as métricas além da tolerância. Ver `docs/modulos/eval.md`.
5. **Dica do usuário vence inferência**, e fica registrada como dica no documento.
6. **Avisar em vez de falhar.** Incerteza vira `warning` no ScoreDoc. Só erro real aborta (ver Score IR).

## 4. Convenções

- **Idiomas:** documentação em português; código, identificadores, comentários e mensagens de commit em inglês.
- **Commits:** Conventional Commits em inglês (`feat(notate): ...`, `fix(listen): ...`, `docs: ...`).
- **Python:** 3.12, `uv`, `ruff` (lint + format), `pytest`, tipagem estrita (`mypy --strict` nos pacotes de domínio).
- **Editor:** TypeScript + React. Tipos da Score IR gerados do JSON Schema, nunca escritos à mão.
- **Testes:** TDD. Todo bug corrigido ganha um teste que o reproduz.
- **Estrutura do código:** ver `docs/arquitetura/stack.md`.

## 5. Como trabalhar uma tarefa

1. Identifique a fase em `docs/roadmap/fases.md` e o(s) módulo(s) em `docs/modulos/`.
2. Leia o `.md` do módulo, a Score IR e só o que for referenciado.
3. Trabalho novo de porte (módulo ou fase) precisa de spec e plano aprovados antes do código.
4. Implemente com testes; rode lint, testes e eval quando aplicável.
5. Atualize a documentação afetada e faça commit.

## 6. O que não fazer

- Não adicione dependência sem checar a licença.
- Não acople um módulo à implementação interna de outro; use a Score IR.
- Não mova lógica de notação para dentro de adaptadores de áudio.
- Não reescreva arquivos de `docs/decisoes/`. Uma decisão nova substitui a antiga num novo ADR.
