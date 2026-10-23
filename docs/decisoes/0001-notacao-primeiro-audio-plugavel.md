# 0001 — Notação primeiro, áudio plugável

**Status:** aceito · **Data:** 2026-10-23

## Contexto
A pesquisa de estado da arte (`../pesquisa/estado-da-arte-2026-10.md`) mostrou que a detecção de notas já tem modelos abertos razoáveis, enquanto a passagem de notas para partitura (quantização, compasso, armadura, grafia, vozes) é a etapa que mais erra, inclusive em produtos comerciais. O projeto é tocado por uma pessoa em meio período.

Alternativas consideradas: (B) pipeline multi-instrumento direto na mix com YourMT3+, descartado por baixa qualidade em orquestra real, código pré-release e custo de GPU contínuo; (C) treinar modelo próprio desde o início, descartado por exigir meses de pesquisa sem produto e sem dados reais.

## Decisão
O núcleo é a Score IR e o motor de notação. Modelos de áudio são adaptadores atrás de interfaces. A v1 trata um instrumento por gravação; multi-instrumento (F5) e modelo próprio (F6) entram depois como adaptadores, alimentados pelos dados do editor.

## Consequências
- Valor entregue cedo e diferencial construído onde o mercado é fraco.
- Orquestra completa só é atendida plenamente na F5/F6.
- Toda troca de modelo é local ao módulo `listen`.
