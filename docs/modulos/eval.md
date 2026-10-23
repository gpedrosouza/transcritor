# eval

**Fase:** F0 (base) e contínuo · **Pacote:** `transcritor_eval`

## Propósito
Medir a qualidade do pipeline e impedir regressões. Nenhuma otimização é aceita sem medição.

## Conjunto de teste
- **F0:** 10–20 trechos monofônicos de orquestra/câmara (flauta, violino, cello, clarinete, oboé...), 15–60 s, com partitura de referência em MusicXML e alinhamento nota-a-nota.
- Fontes: gravações próprias/autorizadas e domínio público com partitura (ex.: IMSLP para partituras; gravações com licença livre). Registrar a licença de cada item em `data/eval/manifest.json`.
- Subconjunto pequeno e rápido para CI; conjunto completo para rodadas manuais.
- Cresce com casos exportados pelo flywheel (F2+).

## Geradores de casos de teste

Partem de partituras de referência (MusicXML de domínio público ou próprias), cujo gabarito é exato por construção.

1. **Gerador de performances simbólicas** (para `notate`, sem áudio): partitura → execução "perfeita" em segundos a um andamento → perturbações parametrizadas que imitam erros do listen e de músicos reais: imprecisão de onset, rubato, accelerando/ritardando, offsets encurtados, notas fragmentadas (vibrato), erros de oitava, notas espúrias de baixa confiança. Gera um ScoreDoc com a camada listen preenchida.
2. **Gerador de áudio sintético** (para `listen` e `rhythm`): partitura → síntese com FluidSynth e banco de timbres de licença comercial (ver `../arquitetura/licencas.md`) → ruído, reverberação e variação de andamento. Reaproveitado na F6 para dados de treino.

Áudio sintético é mais fácil que gravação real e infla métricas: serve para depurar e cobrir casos raros. **O portão de CI usa gravações reais.**

## Métricas
- **Notas (camada listen):** `mir_eval.transcription` (onset F1, F1 com offset, precisão, revocação).
- **Ritmo:** F-measure de beats e downbeats (`mir_eval.beat`); acerto de compasso por segmento.
- **Tonalidade:** acerto de tonalidade (pontuação ponderada MIREX).
- **Notação (criado aqui):** acerto de posição métrica, de duração escrita, de grafia e de acidente exibido, comparando com a referência alinhada.
- **Edição (F2+):** número de operações necessárias e tempo de revisão por minuto de áudio.
- **Simplificação (F2+):** taxa de simplificações de conteúdo revertidas pelo usuário (controle dos limiares do notate).

## Portão de CI
Linha de base versionada em `data/eval/baseline.json`. PR que piore qualquer métrica principal além da tolerância falha; atualizar a linha de base é um commit explícito com justificativa.

## Interface pública
CLI `transcritor-eval run [--subset ci] [--stage listen|rhythm|notate|all]` e relatório em markdown/JSON.

## Dependências
mir_eval (MIT), music21 (BSD), pyfluidsynth / FluidSynth (LGPL-2.1, biblioteca dinâmica), banco de timbres a confirmar.
