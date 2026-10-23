# 0003 — Score IR como contrato único, com camadas listen e notation

**Status:** aceito · **Data:** 2026-10-23

## Contexto
Os módulos precisam ser trocáveis (adaptadores), reprocessáveis por trecho e editáveis por um usuário, e as correções precisam virar dados de treino distinguindo erro de escuta e erro de notação.

## Decisão
Todos os módulos leem e escrevem um único documento, o ScoreDoc (`../arquitetura/score-ir.md`), com camadas separadas para o que foi ouvido (segundos, Hz) e como se escreve (compassos, grafia), IDs estáveis, avisos e proveniência. O editor envia operações sobre IDs, nunca o documento inteiro. Cada etapa é uma função `ScoreDoc → ScoreDoc`.

## Consequências
- Testes isolados por módulo e reprocessamento parcial.
- O schema é ponto único de mudança: exige versionamento e migração.
- Tipos do editor gerados automaticamente do schema.
