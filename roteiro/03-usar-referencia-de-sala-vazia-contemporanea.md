---
titulo: 03 · Usar referência de sala vazia contemporânea
fase: Fase 1 — Investigação
labels: investigação
---

## Depende de

{02} — só faz sentido se a deriva for confirmada.

## Contexto

Hoje todas as features são distâncias DTW contra **uma** referência, a sala
vazia do participante 001. Se o ambiente derivou, essa referência é inadequada
para participantes coletados meses depois.

O uso real do método é calibrar o sistema com a sala vazia **no momento** e
então detectar presença. Uma referência contemporânea é mais fiel a isso — e
provavelmente é o que os autores tinham implicitamente, já que o LATINCOM
trabalhou com 25 participantes num período curto.

## O que fazer

- Para cada participante, usar como referência a sala vazia de um
  participante **vizinho no tempo** (por exemplo, o anterior), nunca a do
  próprio participante — senão a classe 0 vira distância de si mesmo.
- Rodar apenas o protocolo por participante (holdout), com segmentos de 29
  amostras, sem sobreposição.
- Comparar com o resultado da referência única.

## Concluído quando

- [ ] Opção implementada em `build_dataset`, sem remover a referência única
- [ ] Comparação registrada no `DIARIO.md`
- [ ] Decisão registrada no `DECISOES.md`
