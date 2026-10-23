# rhythm

**Fase:** F1 · **Pacote:** `transcritor_rhythm`

## Propósito
Preencher `timeline`: beats, downbeats, curva de tempo e segmentos de compasso.

## Responsabilidades
- Adaptador de beat tracking (`BeatTracker` protocol); padrão: Beat This! (código MIT; pesos a confirmar, ver licenças). Alternativa sem modelo: tempograma do librosa (ISC).
- Curva de BPM a partir dos intervalos entre beats (não um BPM global, que erra por oitava).
- **Inferência de compasso (criado aqui):** a partir dos downbeats e da acentuação, propor numerador e denominador por segmento, incluindo compassos compostos (6/8) e mudanças. Nenhuma ferramenta aberta faz isso de forma confiável.
- Anacruse: posicionar o primeiro downbeat.
- Respeitar dicas de compasso, BPM e anacruse.

## Fontes conhecidas de erro
Rubato e fermatas (orquestra), tercinas que confundem a grade, gravações sem percussão (beat tracking depende de ataques). Tudo isso vira warning com localização.

## Interface pública
`BeatTracker.track(audio) -> (beats, downbeats)`; stage `rhythm.run(doc, audio, config)`.

## Dependências
beat-this (MIT, pesos a confirmar), librosa (ISC).

## Testes
Cliques sintéticos em 2/4, 3/4, 4/4, 6/8 e mudança de compasso; trechos reais com rubato do eval.
