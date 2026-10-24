# core

**Fase:** F0 · **Pacote:** `transcritor_core`

## Propósito
Define a Score IR (ver `../arquitetura/score-ir.md`) e o que todos os módulos compartilham.

## Responsabilidades
- Modelos Pydantic do ScoreDoc, Hints e Op; geração do JSON Schema.
- Serialização/deserialização e migração entre `schema_version`.
- Catálogo de instrumentos: nome, família, transposição, extensão escrita e real, claves usuais.
- Hierarquia de erros (`TranscritorError` e subclasses) e códigos de warning.
- Protocolo `Stage`: `run(doc: ScoreDoc, config) -> ScoreDoc` e registro de proveniência.
- Utilitários de tempo/altura (Hz ↔ MIDI, frações musicais).

## Fora do escopo
Qualquer processamento de áudio ou decisão de notação.

## Interface pública
Exportada em `transcritor_core.__all__`:
- Modelos: `ScoreDoc`, `Source`, `AudioInfo`, `Hints` (`KeyHint`, `MeterHint`, `RegionHint`, `InstrumentCount`), `Part`, `Note`, `ProducedBy`, `Timeline` (`TempoPoint`, `MeterSegment`), `Tonality` (`KeySegment`), `Notation`, `NotatedElement`, `Spelling`, `Tuplet`, `Decision`, `DocWarning`, `WarningCode`, `Location`, `ProvenanceEntry`, `Op`, `OpKind`; constante `SCHEMA_VERSION`.
- E/S: `load(path)`, `dump(doc, path)`, `migrate(doc)`.
- Erros: `TranscritorError`, `SchemaVersionError`.
- Estágios: `Stage`, `run_stage`.
- Utilitários: `instruments` (`instruments.get(name)`), `MusicalFraction`, `hz_to_midi`, `midi_to_hz`, `__version__`.

O JSON Schema do `ScoreDoc` fica em `packages/core/schema/scoredoc.schema.json` (o de `Op` vem na F2). Convenções de posição e versão: ver `../arquitetura/score-ir.md`.

## Dependências
pydantic (MIT).

## Testes
Round-trip de serialização; validação do schema; migração; catálogo de instrumentos (transposições conhecidas).
