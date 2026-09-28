---
titulo: 08 · Seleção de atributos sem vazamento
fase: Fase 2 — Consolidação
labels: investigação
---

## Contexto

O LATINCOM relata que 5 atributos selecionados atingem 99,98% com RF, e que
acima de 20 a acurácia declina. A seleção rodada até agora usou a divisão
aleatória, que está sujeita a vazamento quando há sobreposição.

## O que fazer

- Rodar `SelectKBest` com k em 5, 10, 20, 50, 100, 234.
- Features de 29 amostras, sem sobreposição.
- Protocolo por participante, com a seleção ajustada **apenas no treino**.

## Concluído quando

- [ ] Curva registrada no `DIARIO.md`
- [ ] Comparação com a Figura 3 do LATINCOM
