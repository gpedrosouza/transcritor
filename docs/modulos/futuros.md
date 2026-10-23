# Módulos futuros

## separate (F5)

Separação de fontes como etapa opcional antes de `listen`, ativada só onde o eval mostrar ganho. Candidatos: BS-RoFormer via `audio-separator` ou `msst` (MIT; pesos a confirmar). Para orquestra, separação por família de instrumentos é mais realista do que por instrumento. Decisão depende do experimento comparativo da F5 (separar e transcrever vs. transcrição direta multi-instrumento).

## train (F6)

Treino de modelo próprio de transcrição, de licença comercial, com:
- dados do flywheel (correções reais alinhadas);
- áudio orquestral sintético renderizado a partir de MIDIs/MusicXML de domínio público com bancos de timbres de licença comercial, com ruído e reverberação;
- ponto de partida em arquitetura aberta permissiva (ex.: MT3, Apache-2.0).

Substitui adaptadores de licença frágil. Exige orçamento de GPU e revisão jurídica dos dados.
