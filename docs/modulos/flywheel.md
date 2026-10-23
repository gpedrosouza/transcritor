# flywheel

**Fase:** F2 (coleta) → F6 (treino) · **Pacote:** `transcritor_flywheel`

## Propósito
Transformar correções de usuários em dataset de treino e avaliação. É o ativo estratégico que viabiliza um modelo próprio de licença comercial.

## Responsabilidades
- Registrar, por documento: áudio (referência), ScoreDoc original, sequência de operações e ScoreDoc final aprovado.
- Classificar cada correção pela camada (listen vs. notation vs. timeline vs. tonality): erros de escuta e de notação alimentam melhorias diferentes.
- Consentimento explícito do usuário e termos de uso que permitam uso para treino; respeitar retirada de consentimento.
- Exportar recortes para o `eval` (novos casos de teste) e para o `train` (F6).
- Métricas agregadas: onde o sistema mais erra, por instrumento e por regra do notate.

## Restrições
- Áudio enviado pode ter direitos autorais de terceiros: o uso para treino depende dos termos e deve ser revisado juridicamente antes da F6.
- LGPD: dados pessoais mínimos, separados do dataset.

## Interface pública
`record(doc_id, ops, final_doc, consent)`, `export_eval_cases(filter)`, `stats()`.

## Testes
Integridade (ops reproduzem o documento final); respeito ao consentimento; anonimização.
