# Score IR (ScoreDoc)

Contém: o contrato de dados único entre todos os módulos (ADR 0003). Mudanças aqui exigem incremento de `schema_version` e ADR se quebrarem compatibilidade.

## Formato

Um documento JSON por transcrição, definido em Pydantic no pacote `core`. Dele são gerados o JSON Schema (`core/schema/scoredoc.schema.json`) e os tipos TypeScript do editor.

```
ScoreDoc
├─ schema_version: str            # semver do contrato
├─ id: str
├─ source
│   ├─ audio: {sha256, duration_s, sample_rate, channels, original_name}
│   └─ hints: Hints               # dadas pelo usuário; prevalecem sobre inferência
├─ parts[]: Part
│   ├─ id, instrument (catálogo), transposition_semitones, range_midi: [lo, hi]
│   └─ notes[]: Note              # camada listen
│       ├─ id                     # estável
│       ├─ onset_s, offset_s
│       ├─ pitch_hz, pitch_midi   # pitch_midi pode ser fracionário antes de arredondar
│       ├─ velocity: 0..127 | null
│       ├─ confidence: 0..1
│       └─ produced_by: {adapter, version}
├─ timeline                       # módulo rhythm
│   ├─ beats_s[], downbeats_s[]
│   ├─ tempo_curve[]: {time_s, bpm}
│   └─ meter_segments[]: {start_measure, numerator, denominator, confidence, from_hint}
├─ tonality
│   └─ key_segments[]: {start_measure, tonic, mode, confidence, from_hint}
├─ notation                       # módulo notate; uma entrada por elemento escrito
│   └─ elements[]: NotatedElement
│       ├─ id, note_ids[]         # notas da camada listen que originaram o elemento
│       ├─ kind: note | chord | rest | tie
│       ├─ part_id, staff, voice
│       ├─ measure, beat (fração)  # posição métrica
│       ├─ written_duration (fração de semibreve), tuplet: {actual, normal} | null
│       ├─ spelling[]: {step, alter, octave}   # grafia escrita (já transposta)
│       ├─ accidental_shown: bool
│       └─ decision: {rule, reason}            # por que foi escrito assim
├─ warnings[]: {code, severity, location: {part_id?, note_id?, measure?}, message}
└─ provenance[]: {stage, module_version, adapter, params, started_at, duration_ms}
```

## Hints

```
Hints: {
  instruments?: [{instrument, count}],
  key?: {tonic, mode},
  meter?: {numerator, denominator},
  bpm?: number,
  pickup_beats?: number,        # anacruse
  regions?: [{start_s, end_s, hints}]   # dicas locais
}
```

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
