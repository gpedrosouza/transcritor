# editor

**Fase:** F2 · **App:** `apps/editor`

## Propósito
Onde o arranjador revisa e corrige a transcrição com o áudio sincronizado. É o produto visível e a fonte de dados do flywheel.

## Responsabilidades
- Renderizar a partitura (Verovio WASM) e tocar o áudio original com cursor sincronizado (mapeamento compasso/tempo ↔ segundos via `timeline`).
- Alternar entre áudio original, síntese da transcrição e ambos sobrepostos (comparar de ouvido).
- Destacar warnings e notas de baixa confiança; navegar entre eles.
- Edição: altura, grafia, duração, inserir/remover nota, compasso, tonalidade, barra de compasso. Cada edição vira uma `Op` (ver Score IR).
- Pedir reprocessamento de um trecho com novas dicas ("aqui é 6/8", "modulou para Ré menor").
- Mostrar o `decision.reason` de um elemento ("por que Fá# e não Solb?").
- Exportar MusicXML/PDF.
- Instrumentar tempo de revisão por trecho (métrica de sucesso da F2).

## Princípios
- Sempre operações, nunca reenviar o documento inteiro.
- Desfazer/refazer local sobre a pilha de operações.
- Tipos gerados do JSON Schema.

## Dependências
React (MIT), Vite (MIT), Verovio (LGPL-3.0, WASM dinâmico).

## Testes
Unitários de mapeamento tempo ↔ posição e de geração de ops; testes de componente; teste de uso com arranjador real (critério da F2).
