# listen

**Fase:** F1 (monofônico), F4 (polifônico de um instrumento), F5 (multi-instrumento) · **Pacote:** `transcritor_listen`

## Propósito
Preencher a camada listen: eventos de nota com onset, offset, altura, velocity e confiança, por parte.

## Responsabilidades
- Definir o protocolo `Transcriber` e escolher o adaptador conforme instrumento e configuração.
- Adaptadores:
  - **F1:** `CrepeTranscriber` (torchcrepe, contorno de altura) + segmentação de notas própria (onsets, estabilidade de altura, vibrato, legato); `BasicPitchTranscriber` como alternativa.
  - **F4:** `TranskunTranscriber` (piano).
  - **F5:** `YourMT3Transcriber` (servidor, GPL, exceção em `licencas.md`).
- Restringir notas à extensão do instrumento informado (fora da extensão vira warning, não descarte).
- Reprocessamento parcial por janela de tempo.

## O que é criado aqui
A segmentação de notas monofônicas a partir do contorno de altura é código próprio: é onde instrumentos de sopro e cordas (vibrato, glissando, legato) mais erram em modelos genéricos.

## Fora do escopo
Quantização, compasso, grafia. Saída é em segundos e Hz.

## Interface pública
```python
class Transcriber(Protocol):
    name: str; version: str; weights_license: str
    supports: set[InstrumentFamily]
    def transcribe(self, audio: AudioBuffer, part: Part, hints: Hints,
                   window: TimeWindow | None = None) -> list[Note]: ...
```
Stage: `listen.run(doc, audio, config) -> ScoreDoc`.

## Dependências
torchcrepe (MIT), basic-pitch (Apache-2.0), transkun (MIT, F4).

## Testes
Sinais sintéticos (senoides, escalas, vibrato); trechos reais do eval; contrato de licença do adaptador.
