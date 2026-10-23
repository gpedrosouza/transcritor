# 0002 — Produto comercial e política de licenças

**Status:** aceito · **Data:** 2026-10-23

## Contexto
O produto será comercial, atendendo arranjadores (editor) e desenvolvedores (API). Vários dos melhores modelos abertos têm pesos não comerciais (MuScriptor, madmom, Essentia/MTG, ADTOF) ou licença copyleft (YourMT3+ GPL-3.0, Essentia AGPL).

## Decisão
Adotar a política de `../arquitetura/licencas.md`: permissivas liberadas; LGPL com ligação dinâmica; GPL só no servidor, em processo separado e com exceção registrada; AGPL e pesos não comerciais proibidos. Verificação automática no CI.

## Consequências
- O núcleo fica livre de risco de licença; modelos de licença frágil ficam isolados e substituíveis.
- Algumas opções de maior acurácia ficam indisponíveis, o que reforça o valor do flywheel e do modelo próprio (F6).
- Validação jurídica necessária antes da comercialização.
