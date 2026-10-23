# export

**Fase:** F1 · **Pacote:** `transcritor_export`

## Propósito
Gerar arquivos a partir do ScoreDoc.

## Responsabilidades
- **MusicXML** (formato principal) a partir da camada notation, via music21 ou escrita direta. Partes, claves, armaduras, compassos, quiálteras, ligaduras.
- **MIDI** a partir da camada listen (performance) ou notation (quantizado), à escolha.
- **PDF** via `mscore` no servidor (exceção GPL em `licencas.md`), **validando** que o arquivo foi escrito: o MuseScore pode sair com código 0 sem gerar nada.
- Partes individuais por instrumento.

## Fora do escopo
Decisões de notação (são do notate: export só traduz).

## Interface pública
`to_musicxml(doc) -> bytes`, `to_midi(doc, layer) -> bytes`, `to_pdf(doc, part_id=None) -> bytes`.

## Erros
`ExportToolError` (ferramenta externa falhou ou não gerou saída).

## Dependências
music21 (BSD), MuseScore 4 CLI (GPL, subprocesso).

## Testes
MusicXML válido contra o XSD; reabrir no music21 e comparar; PDF não vazio; round-trip ScoreDoc → MusicXML → leitura.
