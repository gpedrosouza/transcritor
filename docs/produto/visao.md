# Visão do produto

Contém: propósito, clientes, critério de sucesso, restrições e fora de escopo.

## Propósito

Reduzir drasticamente o tempo que um arranjador gasta para transcrever gravações de orquestra e música de câmara. O sistema entrega um rascunho de grade e um editor onde o arranjador corrige com o áudio sincronizado. Cada correção melhora o sistema.

## Clientes

1. **Arranjadores e grupos** (orquestras, conjuntos de câmara): primeiro cliente, atendido pelo editor assistido.
2. **Desenvolvedores**: consomem a transcrição via API pública (fase F3).

## Critério de sucesso da v1

O arranjador sobe uma gravação, informa a formação se quiser, recebe a partitura no editor e chega a uma transcrição correta **mensuravelmente mais rápido** do que transcrevendo do zero. Isso é medido em teste com arranjador real (ver `roadmap/fases.md`, F2).

## Restrições

- **Produto comercial.** Ver `arquitetura/licencas.md`.
- **Repertório-alvo:** orquestra e câmara. A separação de instrumentos desse repertório é fraca no estado da arte (cordas ~5 dB SDR), então a v1 não depende dela.
- **Equipe:** um desenvolvedor, meio período. Escopo de cada fase deve caber nisso.

## Vantagens a explorar

- O arranjador normalmente conhece a formação e, às vezes, a tonalidade e o compasso. Essas dicas entram no pipeline e prevalecem sobre a inferência.
- A detecção de tonalidade é mais confiável em música erudita (~97% na literatura).
- As correções no editor geram pares (áudio, partitura correta), dado raro que permite treinar um modelo próprio de licença comercial (F6).

## Fora de escopo (por ora)

- Partitura final sem revisão humana.
- Transcrição de letra, cifras pop, tablatura.
- Separação de instrumentos de orquestra na v1.
- Tempo real (transcrição ao vivo).
