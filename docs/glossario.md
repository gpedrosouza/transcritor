# Glossário

Contém: termos musicais e técnicos com o sentido usado neste projeto.

## Musicais

- **Armadura de clave:** acidentes fixos no início da pauta, que valem para toda a peça ou seção.
- **Acidente ocorrente:** sustenido, bemol ou bequadro escrito junto à nota, válido até o fim do compasso.
- **Grafia (pitch spelling):** escolha do nome da nota para uma mesma altura (Fá# vs Solb). Depende da tonalidade e do contexto harmônico.
- **Fórmula de compasso (meter):** agrupamento de tempos (2/4, 3/4, 6/8...). Pode mudar ao longo da peça.
- **Anacruse:** notas antes do primeiro tempo forte.
- **Grade:** partitura com todos os instrumentos sobrepostos.
- **Instrumento transpositor:** escreve em altura diferente da que soa (clarinete em Si♭, trompa em Fá).
- **Voz:** linha melódica independente dentro de uma mesma pauta.

## Técnicos

- **Contrato:** acordo sobre o formato dos dados trocados entre módulos (campos, tipos e significado). Quem produz garante o formato; quem consome depende só dele, sem conhecer a implementação do outro. No projeto, o contrato é a Score IR; mudanças nele são versionadas por `schema_version`.
- **ADR (Architecture Decision Record):** registro curto de uma decisão de arquitetura, com contexto, decisão e consequências. Fica em `decisoes/`. Um ADR aceito não é editado; uma decisão nova gera outro ADR que indica qual substitui.
- **ScoreDoc / Score IR:** documento interno que carrega tudo sobre uma transcrição. Ver `arquitetura/score-ir.md`.
- **Camada listen:** o que foi ouvido (tempo em segundos, altura em Hz/MIDI).
- **Camada notation:** como se escreve (compasso, tempo, duração escrita, grafia, voz, pauta).
- **Adaptador:** implementação concreta de uma interface de módulo que usa uma biblioteca ou modelo externo.
- **Dica (hint):** informação dada pelo usuário (formação, tonalidade, compasso, BPM).
- **Operação de edição (op):** correção feita no editor, registrada sobre o ID de um elemento.
- **Onset / offset:** início e fim de uma nota.
- **F1 de notas:** métrica padrão de transcrição (`mir_eval`): onset F1 considera só o início; F1 com offset exige também o fim.
- **SDR:** métrica de qualidade de separação de fontes, em dB.
- **Flywheel:** ciclo em que correções de usuários viram dados de treino que melhoram o sistema.
