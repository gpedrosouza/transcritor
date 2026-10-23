# notate ⭐

**Fase:** F1 (monofônico), F4 (vozes e duas pautas) · **Pacote:** `transcritor_notate`

## Propósito
Transformar a camada listen + timeline + tonality na camada notation: a partitura bem escrita. **É o diferencial do produto.**

## Responsabilidades (em ordem de pipeline)
1. **Tonalidade:** estimar `key_segments` (perfis Krumhansl/Temperley via partitura ou music21), por janela, para detectar modulações. Dica do usuário prevalece.
2. **Quantização:** mapear onsets/offsets para a grade de beats com divisões binárias e ternárias; detectar quiálteras; ligar notas que cruzam barras. Prefere a grade mais simples **só** quando a diferença de ajuste para uma grade mais fina for pequena (mesmo cuidado da etapa 7).
3. **Grafia (pitch spelling):** escolher o nome de cada nota pela tonalidade local e pelo contexto melódico (ps13 do partitura como base).
4. **Acidentes:** decidir quais acidentes aparecem (armadura vs. ocorrente, bequadros, acidentes de cortesia).
5. **Transposição:** escrever na altura do instrumento transpositor.
6. **Vozes e pautas (F4):** separar vozes e distribuir em pautas.
7. **Simplificação:** ver seção abaixo.

Cada decisão grava `decision: {rule, reason}` no elemento, para o editor explicar e para o flywheel aprender com as correções.

## Simplificação: escrita vs. conteúdo

Risco a evitar: o motor "limpar" o que o músico tocou de fato, escondendo falta de acurácia sob uma partitura aparentemente simples.

- **Simplificação de escrita (sempre permitida):** muda só a representação, nunca o que soa. Ex.: semínima ligada a colcheia → semínima pontuada; agrupamento de colcheias segundo o compasso; escolha de clave.
- **Simplificação de conteúdo (restrita):** fundir fragmentos, absorver notas muito curtas, trocar ritmo por um mais simples. Só ocorre quando **todas** as condições valem:
  1. duração abaixo de um limiar calculado do andamento local e da menor subdivisão plausível do trecho;
  2. confiança baixa na camada listen;
  3. padrão conhecido de artefato (ex.: fragmentos de mesma altura separados por intervalo mínimo, típico de vibrato ou rearticulação mal detectada).

Toda simplificação de conteúdo: gera warning `SIMPLIFIED`, registra `decision`, é reversível no editor e **nunca apaga notas da camada listen**. Limiares são parâmetros de configuração, ajustados pelo eval.

Métrica de controle: **taxa de simplificações revertidas pelo usuário** (ver `eval.md`). Se subir, os limiares estão agressivos.

## Princípios
- Determinístico e testável: mesma entrada, mesma saída.
- Regras configuráveis por perfil de repertório (ex.: barroco, romântico).
- Reprocessamento parcial por intervalo de compassos.

## Fora do escopo
- **Leitura de áudio:** feita por `ingest` (decodificação), `listen` (notas) e `rhythm` (beats). O notate recebe tudo pronto no ScoreDoc.
- **Renderização gráfica:** feita por `export` (MusicXML/PDF) e `editor` (Verovio no navegador).

Isso é deliberado: sem áudio e sem desenho, o notate é lógica pura e determinística, testável com milhares de casos em segundos.

## Interface pública
Stage `notate.run(doc, config, measures: range | None = None) -> ScoreDoc`; subfunções públicas por etapa (`estimate_key`, `quantize`, `spell`, `place_accidentals`) para teste e reuso.

## Dependências
partitura (Apache-2.0), music21 (BSD).

## Testes
Maior suíte do projeto, **sem áudio**:
- **Unitários por regra:** tercinas, anacruse, síncope, modulação, cromatismo ascendente vs. descendente, instrumentos transpositores, casos de simplificação permitida e proibida.
- **Gerador de performances simbólicas** (pacote `eval`, ver `eval.md`): partitura de referência → execução em segundos → perturbações → notate → comparação com a referência. Gabarito exato por construção.
- **Golden files** e métricas de notação do eval sobre gravações reais.
