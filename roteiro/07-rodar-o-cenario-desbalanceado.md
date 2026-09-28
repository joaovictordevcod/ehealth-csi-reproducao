---
titulo: 07 · Rodar o cenário desbalanceado
fase: Fase 2 — Consolidação
labels: investigação
---

## Contexto

O escopo inclui dados balanceados **e** desbalanceados. O desbalanceado ainda
não foi executado.

No LATINCOM, o NB registra 79,41% de acurácia no desbalanceado, mas 46,55% de
precisão e 44,26% de F-measure — a acurácia esconde que o modelo classifica
quase tudo como a classe majoritária.

## O que fazer

- Usar **gravações completas** (500 amostras) nas duas classes, sem
  fragmentar: 1700 ocupadas contra ~100 vazias. Isso elimina a sobreposição e
  usa todo o sinal disponível.
- Reportar acurácia, precisão, recall e F1 — não só acurácia.
- Avaliar nos dois protocolos.

## Concluído quando

- [ ] Resultado registrado no `DIARIO.md`
- [ ] Comparação qualitativa com o padrão relatado no LATINCOM
