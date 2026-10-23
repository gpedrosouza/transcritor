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
`ScoreDoc`, `Hints`, `Op`, `Stage`, `instruments.get(name)`, `errors`, `load(path)`, `dump(doc, path)`, `migrate(doc)`.

## Dependências
pydantic (MIT).

## Testes
Round-trip de serialização; validação do schema; migração; catálogo de instrumentos (transposições conhecidas).
