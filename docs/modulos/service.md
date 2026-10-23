# service

**Fase:** F2 (interno, para o editor) → F3 (API pública) · **App:** `apps/service`

## Propósito
Backend que executa o pipeline como jobs e serve o editor. Na F3, a mesma base vira a API pública, sem retrabalho.

## Responsabilidades
- Upload de áudio e dicas; criação de job com ID; consulta de status; resultado (ScoreDoc e arquivos exportados).
- Aplicar operações de edição ao ScoreDoc, versionar o documento e disparar reprocessamento parcial.
- Repassar operações e áudio ao `flywheel` (com consentimento).
- Armazenamento: local no início; interface preparada para objeto (S3 compatível).
- **F3:** autenticação por chave, cotas, documentação OpenAPI pública, webhooks de conclusão.

## Endpoints (F2, rascunho)
`POST /jobs` · `GET /jobs/{id}` · `GET /docs/{id}` · `POST /docs/{id}/ops` · `GET /docs/{id}/export/{fmt}` · `GET /audio/{id}`

## Princípios
- Jobs assíncronos: pipeline nunca roda dentro da requisição HTTP.
- Workers separados por ambiente quando dependências conflitarem (ex.: modelos com versões de Python diferentes).
- Logs sem conteúdo de áudio; métricas de duração por etapa.

## Dependências
FastAPI (MIT), uvicorn (BSD).

## Testes
Testes de API com pipeline simulado; aplicação de operações; idempotência; recuperação de job interrompido.
