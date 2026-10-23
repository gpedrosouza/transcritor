# 0004 — Editor assistido antes da API pública

**Status:** aceito · **Data:** 2026-10-23

## Contexto
A proposta inicial previa a API (mais simples) antes do editor. O critério de sucesso da v1 é o editor assistido, e o feedback de acurácia vem das correções dos usuários.

## Decisão
O editor e o flywheel formam a F2; a API pública passa para a F3. O backend do editor nasce como serviço interno e evolui para a API pública, sem retrabalho.

## Consequências
- Dados de correção desde cedo, alimentando o eval e, depois, o treino.
- A F2 fica maior; a receita via API começa mais tarde.
