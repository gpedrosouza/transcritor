# Política de licenças

Contém: o que pode entrar no produto e como isso é verificado (ADR 0002). Não é aconselhamento jurídico; validar com advogado antes de comercializar.

## Regra geral

O produto é comercial e roda como serviço (servidor + editor web).

| Categoria | Situação |
|---|---|
| MIT, BSD, Apache-2.0, ISC | Permitido em qualquer lugar |
| LGPL | Permitido com ligação dinâmica (ex.: Verovio WASM carregado no editor) |
| GPL-3.0 | Só no servidor, em processo separado, nunca distribuído ao usuário. Exige exceção registrada abaixo |
| AGPL | Proibido |
| Pesos de modelo CC BY-NC / NC-SA ou "research only" | Proibido |
| Sem licença declarada | Proibido até haver licença explícita |

Código e **pesos** são avaliados separadamente: um repositório MIT pode ter pesos não comerciais.

## Exceções aprovadas

| Componente | Licença | Uso | Condição |
|---|---|---|---|
| MuseScore 4 (`mscore`) | GPL-3.0 | Gerar PDF no servidor | Chamado por subprocesso, não distribuído |
| YourMT3+ (F5, experimental) | GPL-3.0 | Adaptador `listen` no servidor | Processo separado; reavaliar antes de ativar |

## Proibidos conhecidos

Pesos do MuScriptor, modelos do madmom, Essentia (AGPL) e seus modelos MTG, ADTOF, SheetSage v1, pesos `umxl` do Open-Unmix.

## Pendente de verificação antes do uso

- Pesos do Beat This! (código MIT): confirmar antes da F1.
- Pesos do BS-RoFormer SW e checkpoints do MVSep: confirmar antes da F5.
- Banco de timbres para o gerador de áudio sintético (candidato: MuseScore_General): confirmar antes de usar no eval e, principalmente, antes de gerar dados de treino (F6).

## Verificação automática

- CI roda checagem de licenças das dependências Python e npm contra uma lista de permitidas.
- Cada adaptador declara `weights_license` no código; um teste falha se a licença não estiver na lista permitida.
- Adicionar exceção exige ADR.
