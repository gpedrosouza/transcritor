# notate ⭐

**Fase:** F1 (monofônico), F4 (vozes e duas pautas) · **Pacote:** `transcritor_notate`

## Propósito
Transformar a camada listen + timeline + tonality na camada notation: a partitura bem escrita. **É o diferencial do produto.**

## Responsabilidades (em ordem de pipeline)
1. **Tonalidade:** estimar `key_segments` (perfis Krumhansl/Temperley via partitura ou music21), por janela, para detectar modulações. Dica do usuário prevalece.
2. **Quantização:** mapear onsets/offsets para a grade de beats com divisões binárias e ternárias, escolhendo a mais simples que explique o ritmo dentro de uma tolerância; detectar quiálteras; ligar notas que cruzam barras.
3. **Grafia (pitch spelling):** escolher o nome de cada nota pela tonalidade local e pelo contexto melódico (ps13 do partitura como base).
4. **Acidentes:** decidir quais acidentes aparecem (armadura vs. ocorrente, bequadros, acidentes de cortesia).
5. **Transposição:** escrever na altura do instrumento transpositor.
6. **Vozes e pautas (F4):** separar vozes e distribuir em pautas.
7. **Simplificação:** fundir fragmentos rítmicos implausíveis; registrar cada simplificação.

Cada decisão grava `decision: {rule, reason}` no elemento, para o editor explicar e para o flywheel aprender com as correções.

## Princípios
- Determinístico e testável: mesma entrada, mesma saída.
- Regras configuráveis por perfil de repertório (ex.: barroco, romântico).
- Reprocessamento parcial por intervalo de compassos.

## Fora do escopo
Leitura de áudio; renderização gráfica.

## Interface pública
Stage `notate.run(doc, config, measures: range | None = None) -> ScoreDoc`; subfunções públicas por etapa (`estimate_key`, `quantize`, `spell`, `place_accidentals`) para teste e reuso.

## Dependências
partitura (Apache-2.0), music21 (BSD).

## Testes
Maior suíte do projeto: casos unitários por regra (tercinas, anacruse, síncope, modulação, cromatismo ascendente vs. descendente, instrumentos transpositores), golden files e métricas de notação do eval.
