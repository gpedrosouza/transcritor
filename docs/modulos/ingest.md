# ingest

**Fase:** F1 · **Pacote:** `transcritor_ingest`

## Propósito
Transformar um arquivo enviado e as dicas do usuário num ScoreDoc inicial válido.

## Responsabilidades
- Decodificar formatos comuns (wav, flac, mp3, m4a, ogg) via ffmpeg/soundfile.
- Normalizar: mono, taxa de amostragem de trabalho (definida pelos adaptadores), normalização de nível.
- Calcular `sha256`, duração e metadados; preencher `source`.
- Validar e normalizar `Hints` (instrumentos do catálogo, tonalidade, compasso, BPM, anacruse).
- Criar as `parts` a partir das dicas de instrumentos.

## Fora do escopo
Detecção de notas, ritmo ou tonalidade.

## Interface pública
`ingest(audio_path, hints) -> (ScoreDoc, AudioBuffer)`; `AudioBuffer` fica em cache por hash e não vai dentro do JSON.

## Erros
`UnsupportedAudioError`, `CorruptAudioError`, `InvalidHintError`. Áudio muito longo ou silencioso gera warning.

## Dependências
soundfile (BSD), ffmpeg (LGPL, subprocesso).

## Testes
Arquivos curtos de cada formato; dicas inválidas; mono/estéreo; hash estável.
