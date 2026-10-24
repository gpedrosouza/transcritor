# Fases de entrega

Contém: ordem de entrega, escopo e critério de saída de cada fase. Cada fase é um subprojeto com spec (`../specs/`), plano (`../planos/`) e implementação próprios. Uma fase só termina quando atinge o critério de saída **medido no eval**.

Estado atual: **Código da F0 concluído; saída da F0 pendente da curadoria do mono-v1 e da primeira execução verde no GitHub Actions.**

| Fase | Nome | Porte | Módulos |
|---|---|---|---|
| F0 | Fundação | pequeno | core, eval, CI |
| F1 | Monofônico ponta a ponta | médio | ingest, listen, rhythm, notate, export, cli |
| F2 | Editor assistido + flywheel | grande | service (interno), editor, flywheel |
| F3 | API pública | pequeno | service |
| F4 | Polifonia de um instrumento | médio | listen, notate |
| F5 | Multi-instrumento | grande, exploratório | listen, separate |
| F6 | Modelo próprio | pesquisa | train |

O editor vem antes da API (ADR 0004) para obter cedo o feedback de acurácia dos usuários.

## F0 — Fundação
- **Escopo:** repositório (uv workspace, layout de `../arquitetura/stack.md`), CI (lint, tipos, testes, licenças), `core` com Score IR completa e JSON Schema, `eval` com o conjunto monofônico inicial e métricas de notas e notação.
- **Saída:** CI verde; `transcritor-eval` roda sobre um "transcritor nulo" e produz relatório; schema publicado.
- **Verificação de saída:** código da F0 concluído; saída da F0 pendente da curadoria do mono-v1 e da primeira execução verde no GitHub Actions. Localmente: lint, tipos e testes verdes; checagem de licenças ok; `transcritor-eval` roda com o pipeline nulo e gera relatório; um oráculo de teste comprova que uma transcrição correta pontua 1,0 em todas as métricas; schema versionado em `packages/core/schema/scoredoc.schema.json`. Falta a curadoria do conjunto real `mono-v1` (ver `../modulos/eval.md`), onde a F1 mede a linha de base.

## F1 — Monofônico ponta a ponta
- **Escopo:** pipeline completo pela CLI para um instrumento monofônico: `transcritor transcribe audio.wav --instrument flute [--key ... --meter ... --bpm ...]` → MusicXML + PDF.
- **Saída:** no conjunto de teste monofônico, metas definidas na spec da F1 a partir da linha de base medida na F0 (onset F1 de notas, acerto de compasso, de tonalidade e de grafia). MusicXML abre no MuseScore sem correções estruturais.

## F2 — Editor assistido + flywheel
- **Escopo:** `service` interno com jobs e operações; editor com partitura sincronizada, destaque de incertezas, edição por operações, reprocessamento por trecho com dicas, explicação de decisões; flywheel com consentimento.
- **Saída:** em teste com ao menos um arranjador real, transcrever um trecho usando o editor leva mensuravelmente menos tempo do que do zero (meta numérica na spec da F2); correções aparecem no flywheel e podem virar casos de eval.

## F3 — API pública
- **Escopo:** autenticação, cotas, OpenAPI pública, webhooks, documentação para desenvolvedores.
- **Saída:** um cliente externo transcreve um arquivo de ponta a ponta usando só a documentação.

## F4 — Polifonia de um instrumento
- **Escopo:** piano e harpa (Transkun), cordas duplas; vozes e duas pautas no notate.
- **Saída:** metas de F1 de notas e de acerto de vozes num conjunto polifônico novo do eval.

## F5 — Multi-instrumento
- **Escopo:** adaptador multi-instrumento condicionado pela formação informada; experimento comparativo "separar e transcrever" vs. "transcrição direta" no eval; adoção do vencedor.
- **Saída:** relatório do experimento e grade de pequena formação de câmara (2–4 instrumentos) com metas definidas na spec.

## F6 — Modelo próprio
- **Escopo:** treino com dados do flywheel + sintéticos (ver `../modulos/futuros.md`).
- **Saída:** modelo de licença comercial que supera o adaptador vigente no eval.

## Ressalva de prazo
Em meio período, F0–F2 já é horizonte de muitos meses. O atendimento pleno de orquestra completa só vem na F5/F6; até lá o valor ao arranjador vem de partes isoladas e de um bom editor.
