# Score IR (ScoreDoc)

Contém: o contrato de dados único entre todos os módulos (ADR 0003). Mudanças aqui exigem incremento de `schema_version` e ADR se quebrarem compatibilidade.

## Formato

Um documento JSON por transcrição, definido em Pydantic no pacote `core`. Dele são gerados o JSON Schema (`core/schema/scoredoc.schema.json`) e os tipos TypeScript do editor.

```
ScoreDoc
├─ schema_version: str            # semver do contrato (MAJOR.MINOR.PATCH)
├─ id: str
├─ source
│   ├─ audio: {sha256, duration_s, sample_rate, channels, original_name}
│   └─ hints: Hints               # dadas pelo usuário; prevalecem sobre inferência
├─ parts[]: Part
│   ├─ id, instrument (catálogo), transposition_semitones, range_midi: [lo, hi]
│   └─ notes[]: Note              # camada listen
│       ├─ id                     # estável
│       ├─ onset_s, offset_s
│       ├─ pitch_hz, pitch_midi   # altura SOANTE; pitch_midi pode ser fracionário antes de arredondar
│       ├─ velocity: 0..127 | null
│       ├─ confidence: 0..1
│       └─ produced_by: {adapter, version}
├─ timeline                       # módulo rhythm
│   ├─ beats_s[], downbeats_s[]
│   ├─ tempo_curve[]: {time_s, bpm}
│   └─ meter_segments[]: {start_measure, numerator, denominator, confidence, from_hint}
├─ tonality
│   └─ key_segments[]: {start_measure, tonic_step, tonic_alter, mode, confidence, from_hint}
├─ notation                       # módulo notate; uma entrada por elemento escrito
│   └─ elements[]: NotatedElement
│       ├─ id, note_ids[]         # notas da camada listen que originaram o elemento
│       ├─ kind: note | chord | rest | tie
│       ├─ part_id, staff, voice
│       ├─ measure, beat (fração)  # posição métrica
│       ├─ written_duration (fração de semibreve, > 0), tuplet: {actual, normal} | null
│       ├─ spelling[]: {step, alter, octave}   # altura ESCRITA (já transposta)
│       ├─ accidental_shown: bool
│       └─ decision: {rule, reason}            # por que foi escrito assim
├─ warnings[]: {code, severity, location: {part_id?, note_id?, measure?}, message}
└─ provenance[]: {stage, module_version, adapter, params, started_at, duration_ms}
```

## Convenções de posição e serialização

- `beat` = deslocamento desde o início do compasso, em fração de semibreve (`>= 0`). Compassos numerados a partir de 1; a anacruse é o compasso 0. Dentro da anacruse, `beat` é o deslocamento desde o início do conteúdo da própria anacruse (a primeira nota fica em `beat` 0, sem alinhar ao fim de um compasso cheio).
- **Compassos são posicionais**: `measure` é a posição do compasso na peça (ou no trecho), não o atributo `number` de um MusicXML. O primeiro compasso é anacruse (índice 0) se e somente se seu conteúdo é mais curto que um compasso cheio da sua fórmula; os demais são 1..N em ordem. Um trecho que começa no compasso 37 do original tem `measure` 1.
- **Altura soante × escrita**: `Note.pitch_hz` e `Note.pitch_midi` são a altura **soante**; `NotatedElement.spelling` é a altura **escrita** (soante − `transposition_semitones` da parte).
- Valores numéricos não podem ser NaN nem infinito. Ids de partes, de notas e de elementos são únicos no documento.
- Ligaduras são elementos separados: o elemento que inicia a ligadura carrega a própria duração escrita do segmento; as continuações são elementos `kind: "tie"`.
- `Op` é serializado com `from` (alias) por padrão. O JSON Schema publicado na F0 cobre apenas o `ScoreDoc`; o schema de `Op` vem na F2.
- `schema_version` deve ser `MAJOR.MINOR.PATCH`. Documentos de outro major, ou de minor/patch mais novo que o do `core`, são rejeitados com `SchemaVersionError`.

## Hints

```
Hints: {
  instruments?: [{instrument, count}],
  key?: {tonic_step, tonic_alter, mode},
  meter?: {numerator, denominator},
  bpm?: number,
  pickup_beats?: MusicalFraction,   # anacruse, string "n/d" em fração de semibreve (mesma unidade de beat), > 0
  regions?: [{start_s, end_s, key?, meter?, bpm?}]   # dicas locais (planas)
}
```

Ex.: `pickup_beats: "1/4"` = anacruse de uma semínima.

## Operações de edição

O editor nunca envia o documento inteiro de volta: envia operações, que o `service` aplica e registra (e o `flywheel` armazena).

```
Op: {
  id, created_at, author,
  layer: "listen" | "notation" | "timeline" | "tonality",
  target_id,                 # id do elemento afetado (ou null para inserção)
  op: "set_pitch" | "set_onset" | "set_offset" | "insert_note" | "delete_note"
      | "set_spelling" | "set_duration" | "set_voice" | "set_meter" | "set_key"
      | "move_barline" | ...,
  from, to                   # valores antes e depois
}
```

Operações nas camadas `timeline` ou `tonality` disparam reprocessamento de `notate` no trecho afetado. Operações em `listen` disparam `notate` só nas notas afetadas.

## Erros e avisos

- **Aviso** (`warnings[]`): incerteza ou anomalia que não impede o resultado. Exemplos: `LOW_CONFIDENCE_NOTE`, `OUT_OF_RANGE`, `AMBIGUOUS_METER`, `KEY_CHANGE_SUSPECTED`, `UNQUANTIZABLE_RHYTHM`, `SIMPLIFIED` (simplificação de conteúdo feita pelo notate; ver `../modulos/notate.md`).
- **Erro** (exceção tipada, job falha): áudio ilegível, formato não suportado, falha de ferramenta externa (ex.: MuseScore não gerou arquivo). Hierarquia em `core.errors`.

## Regras de compatibilidade

- Campos novos opcionais: incremento minor.
- Remover ou mudar semântica: incremento major + ADR + migração.
- Todo ScoreDoc persistido guarda o `schema_version`; o `core` fornece migradores.
