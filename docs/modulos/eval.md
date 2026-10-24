# eval

**Fase:** F0 (base) e contínuo · **Pacote:** `transcritor_eval`

## Propósito
Medir a qualidade do pipeline e impedir regressões. Nenhuma otimização é aceita sem medição.

## Conjuntos e locais
- **`ci`** (sintético, CC0): pequeno e rápido, com áudio versionado. Fica em `packages/eval/datasets/ci/`.
- **`mono-v1`** (real): 10–20 trechos monofônicos de orquestra/câmara (flauta, violino, cello, clarinete, oboé...), 15–60 s, com partitura de referência em MusicXML e alinhamento nota-a-nota. Manifesto e referências em `packages/eval/datasets/mono-v1/`; é curado pelo usuário (ver abaixo).
- Manifestos e referências (CSV de notas, MusicXML, downbeats) ficam em `packages/eval/datasets/<nome>/` e são versionados. O arquivo de downbeats de cada item fica em `refs/` (caminho relativo ao manifesto) e alimenta tanto o alinhamento de notas quanto a métrica de downbeats.
- Linhas de base: `packages/eval/baselines/<subset>.json`.
- Só o áudio real vive em `data/eval/audio/` (fora do git). O manifesto do `mono-v1` usa `audio_root: "data"`; o do `ci` usa `audio_root: "manifest"`.
- Cada item registra licença e fonte no manifesto. O conjunto cresce com casos exportados pelo flywheel (F2+).

## Geradores de casos de teste (adiados para a F1)

Partem de partituras de referência (MusicXML de domínio público ou próprias), cujo gabarito é exato por construção. **Não existem na F0**; o `ci` usa uma fixture sintética simples (`packages/eval/scripts/make_ci_fixture.py`).

1. **Gerador de performances simbólicas** (para `notate`, sem áudio): partitura → execução "perfeita" → perturbações parametrizadas (imprecisão de onset, rubato, offsets encurtados, notas fragmentadas, erros de oitava, notas espúrias). Gera um ScoreDoc com a camada listen preenchida.
2. **Gerador de áudio sintético** (para `listen` e `rhythm`): partitura → síntese com FluidSynth e banco de timbres de licença comercial (ver `../arquitetura/licencas.md`) → ruído, reverberação e variação de andamento.

Áudio sintético infla métricas: serve para depurar e cobrir casos raros. **O portão de CI da F1 em diante usa gravações reais.**

## Métricas (implementadas na F0)

### Notas (camada listen)
`mir_eval.transcription`:
- onset F1, com tolerância de onset de 50 ms e de altura de 50 cents;
- F1 com offset (razão de offset 0,2);
- F1 de downbeats (`mir_eval.beat`), janela de 70 ms, contra os **downbeats verdadeiros** da referência: as barras de compasso, ou seja, o arquivo de downbeats **sem** o instante final (fim do último compasso) e **sem** o início da anacruse, quando houver (`measures.reference_downbeats`). O `timeline.downbeats_s` estimado deve seguir a mesma definição: marcar o início da anacruse como downbeat é penalizado.

### Notação
- Compassos indexados **por posição** (ver Score IR): o primeiro compasso é anacruse (0) se e somente se é mais curto que um compasso cheio da sua fórmula; os demais são 1..N. O atributo `number` do MusicXML é ignorado.
- Casamento por posição exata `(measure, beat)`; reporta precisão e revocação de posição.
- Entre os elementos casados: acurácia de duração escrita, de grafia e de acidente exibido.
- A comparação é por segmento escrito de ligadura: continuações (`kind: "tie"`) ficam fora dos dois lados.
- Altura **escrita**, não a soante.
- Acidente exibido = presença do elemento `<accidental>` no MusicXML.
- Notas de adorno (grace notes) são ignoradas.

### Ritmo e tonalidade
- `key_score`: pontuação ponderada MIREX, com mapeamento enarmônico quando o `mir_eval` não tem o nome da tônica.
- `meter_accuracy`: por compasso de referência; a anacruse é comparada com a fórmula de compasso vigente.

### Futuras
- **Edição (F2+):** número de operações e tempo de revisão por minuto de áudio.
- **Simplificação (F2+):** taxa de simplificações revertidas pelo usuário.

## Dicas dadas ao pipeline

Por padrão (`run --hints instrument`), o pipeline recebe só o instrumento do item; a tonalidade é estimada, não entregue, e o `key_score` mede a estimativa. Com `--hints all`, a tonalidade de referência do manifesto também é passada como dica (útil para isolar outras camadas). O modo fica registrado no relatório (`hints` no JSON e "Dicas" no cabeçalho do markdown).

## Oráculo

`packages/eval/tests/test_oracle.py` injeta um pipeline-oráculo (só de teste) que monta um ScoreDoc correto a partir das referências; ele precisa pontuar 1,0 em todas as médias do `ci` e de uma partitura com anacruse. Não tem linha de base de CI.

## Portão de CI
Linha de base versionada em `packages/eval/baselines/<subset>.json`. O portão **falha fechado**:
- métrica ausente ou NaN conta como regressão;
- `gate` falha se qualquer item tiver status `error`;
- linha de base vazia ou tolerância inválida (não finita ou negativa) → saída 2;
- `baseline` recusa médias vazias e qualquer item `error` ou `skipped`.

Tolerância padrão: 0,01. PR que piore qualquer métrica além dela falha. Atualizar a linha de base é um commit explícito com justificativa.

## Interface pública (CLI)

```
# rodar o pipeline nulo sobre um conjunto e gerar report.json (+ markdown)
uv run transcritor-eval run --manifest packages/eval/datasets/ci/manifest.json \
    --subset ci --pipeline null --out eval-out [--hints instrument|all]

# comparar com a linha de base (código de saída != 0 em regressão)
uv run transcritor-eval gate --report eval-out/report.json \
    --baseline packages/eval/baselines/ci.json [--tolerance 0.01]

# gravar as médias de um relatório como nova linha de base
uv run transcritor-eval baseline --report eval-out/report.json \
    --out packages/eval/baselines/ci.json

# derivar o CSV de notas de referência a partir do MusicXML + downbeats
uv run transcritor-eval align ref.musicxml ref.downbeats.txt --out ref.notes.csv [--part N]
```

`align --part N` é o índice (base 0, padrão 0) da parte na partitura, não um id MusicXML como `P1`. `run --data-root` tem padrão `data/eval/audio`; em manifestos com `audio_root: "data"`, o campo `audio` do item é relativo a esse diretório (ex.: `"flauta_x.wav"` → `data/eval/audio/flauta_x.wav`). A opção `--stage listen|rhythm|notate|all` fica para a F1; na F0 só existe `--pipeline null`.

## Curadoria do conjunto mono-v1

Trabalho musical do usuário, pode correr em paralelo ao código. Meta: 10–20 itens de 15–60 s. Para cada item:

1. **Escolher a gravação** com licença que permita o uso (domínio público, Creative Commons, ou própria/autorizada).
2. **Obter o MusicXML** (IMSLP, MuseScore ou digitar). A referência deve ser exportada de software de notação (MuseScore/Sibelius/Dorico, ou arquivos do IMSLP), para que as tags `<accidental>` estejam presentes.
   - **Cortar o MusicXML exatamente no trecho gravado.** A numeração de compassos é posicional (o `number` do MusicXML é ignorado), então não é preciso renumerar; mas o trecho deve começar numa barra de compasso ou com uma anacruse (primeiro compasso mais curto que a fórmula).
   - **Escrever por extenso** ritornelos, D.C., D.S. e codas: o número de compassos do MusicXML tem de bater com o arquivo de downbeats.
3. **Marcar os inícios de compasso e o instante final** no Audacity como rótulos e exportar. O arquivo de downbeats lista o início de cada compasso **incluindo a anacruse**, mais o instante final do último compasso (N compassos → N+1 linhas). Formatos aceitos: rótulos do Audacity (separados por tabulação; linhas de seleção espectral, que começam com `\`, são ignoradas) ou um número por linha. Uma linha que não seja um tempo válido gera erro com o número da linha. Na métrica, o início da anacruse e o instante final não contam como downbeats (ver "Notas").
4. **Rodar `transcritor-eval align`** para gerar o CSV de notas de referência. O CSV (`onset_s,offset_s,pitch_midi`) traz a altura **soante** (já transposta para instrumentos transpositores), notas ligadas fundidas numa só e notas de adorno omitidas.
5. **Versionar** MusicXML, CSV e downbeats em `packages/eval/datasets/mono-v1/refs/` e adicionar o item a `packages/eval/datasets/mono-v1/manifest.json`, com licença e fonte. Use `packages/eval/datasets/ci/manifest.json` como modelo. Ids de item repetidos são rejeitados.
6. **Colocar o áudio** em `data/eval/audio/` (nunca é commitado).

Campos de cada item do manifesto (caminhos de `reference_*` relativos ao manifesto; `audio` relativo a `data/eval/audio/`, pois o `mono-v1` usa `audio_root: "data"`):

```json
{
  "id": "flauta_bach_bwv1013_allemande",
  "instrument": "flute",
  "audio": "flauta_bach_bwv1013_allemande.wav",
  "audio_sha256": null,
  "reference_notes": "refs/flauta_bach_bwv1013_allemande.notes.csv",
  "reference_score": "refs/flauta_bach_bwv1013_allemande.musicxml",
  "reference_downbeats": "refs/flauta_bach_bwv1013_allemande.downbeats.txt",
  "key": {"tonic_step": "A", "tonic_alter": 0, "mode": "minor"},
  "license": "CC-BY-4.0",
  "source": "gravação própria, 2026-10; partitura IMSLP #12345",
  "subsets": ["full"]
}
```

- `instrument` deve existir no catálogo do `core` (ex.: `flute`, `violin`, `cello`, `clarinet_bb`, `oboe`).
- `key` é **obrigatório no mono-v1**: sem ele o `key_score` do item é 0. Por padrão ele não é passado ao pipeline (ver "Dicas dadas ao pipeline").
- `subsets: ["full"]` para itens reais (`ci` é só o conjunto sintético).

Rodar o eval no mono-v1:

```
uv run transcritor-eval run --manifest packages/eval/datasets/mono-v1/manifest.json \
    --subset full --pipeline null --out eval-out
```

A F1 começa medindo a linha de base nesse conjunto.

## Dependências
mir_eval (MIT), music21 (BSD). Para os geradores da F1: pyfluidsynth / FluidSynth (LGPL-2.1, biblioteca dinâmica), banco de timbres a confirmar.
