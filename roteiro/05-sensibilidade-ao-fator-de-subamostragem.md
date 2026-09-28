---
titulo: 05 · Sensibilidade ao fator de subamostragem
fase: Fase 1 — Investigação
labels: investigação
---

## Contexto

O pipeline subamostra o DS2 por 4 (de ~33 Hz para ~8,7 Hz) para aproximar a
taxa do DS1 descrita nos artigos e reduzir o custo do DTW. Isso descarta 3/4
das amostras.

## O que fazer

Testar fatores 1, 2, 4 e 8, mantendo a **duração** do segmento constante
(~3,3 s) — ou seja, ajustando `seg_len` em amostras para cada fator.

Atenção ao custo: fator 1 multiplica o tempo do DTW por ~16. Medir numa
amostra de participantes antes de rodar tudo.

## Concluído quando

- [ ] Resultados em `.csv`, versionados
- [ ] Registro no `DIARIO.md`
