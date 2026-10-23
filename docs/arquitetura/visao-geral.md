# Visão geral da arquitetura

Contém: abordagem, módulos, fluxo de processamento, princípios de design.

## Abordagem: notação primeiro, áudio plugável (ADR 0001)

O valor diferencial está em transformar notas em partitura bem escrita (quantização, compasso, armadura vs. acidente ocorrente, grafia, vozes), que é a camada que mais erra nos produtos existentes. A detecção de notas é reaproveitada de modelos abertos de licença permissiva, atrás de adaptadores. Modelos melhores (inclusive o próprio, na F6) entram sem mudar o resto.

## Módulos

| Módulo | Responsabilidade | Doc |
|---|---|---|
| core | Score IR, tipos e utilitários comuns | `modulos/core.md` |
| ingest | Decodificar e normalizar áudio; validar dicas do usuário | `modulos/ingest.md` |
| listen | Áudio → eventos de nota (camada listen) | `modulos/listen.md` |
| rhythm | Beats, downbeats, curva de tempo, proposta de compasso | `modulos/rhythm.md` |
| notate | Eventos + ritmo → notação (camada notation) | `modulos/notate.md` |
| export | MusicXML, MIDI, PDF | `modulos/export.md` |
| service | Backend: upload, jobs, resultado; vira a API pública na F3 | `modulos/service.md` |
| editor | App web: partitura sincronizada ao áudio, correções | `modulos/editor.md` |
| flywheel | Guarda pares áudio + correções como dataset | `modulos/flywheel.md` |
| eval | Conjunto de teste, métricas, portão de CI | `modulos/eval.md` |
| separate, train | Futuros (F5, F6) | `modulos/futuros.md` |

## Fluxo

```
áudio + dicas
   │
 ingest ──► listen ──► rhythm ──► notate ──► export ──► MusicXML / MIDI / PDF
   │          │          │          │
   └──────────┴──── ScoreDoc enriquecido a cada etapa ────► service ──► editor
                                                                         │
                                         operações de correção ◄─────────┘
                                                │
                                   reprocessa etapa/trecho afetado
                                                │
                                            flywheel (dataset)
```

## Princípios

1. **Etapas são funções puras `ScoreDoc → ScoreDoc`.** Cada etapa só acrescenta à sua parte do documento. Isso permite reprocessar só uma etapa ou um trecho, cachear por (hash de entrada, versão do módulo) e testar isoladamente.
2. **Duas camadas separadas.** `listen` (o que foi ouvido) e `notation` (como se escreve) nunca se misturam. Corrigir uma não apaga a outra, e o flywheel sabe se o erro foi de escuta ou de notação.
3. **IDs estáveis.** Notas e elementos têm IDs que sobrevivem ao reprocessamento quando possível, para que operações de correção continuem válidas.
4. **Interfaces pequenas.** Cada módulo expõe poucas funções públicas, documentadas no seu `.md`. Adaptadores implementam protocolos (`typing.Protocol`).
5. **Incerteza é dado.** Baixa confiança vira `warning` com localização no documento; o editor usa isso para guiar a revisão.
6. **Proveniência sempre.** Cada etapa registra módulo, versão, adaptador, parâmetros e duração.
