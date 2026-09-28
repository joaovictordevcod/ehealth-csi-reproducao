---
titulo: 04 · Sensibilidade ao pré-processamento (Hampel e média móvel)
fase: Fase 1 — Investigação
labels: investigação
---

## Contexto

Os artigos não informam as janelas do filtro de Hampel nem da média móvel. Os
valores atuais (7 e 5) foram escolhidos por convenção. É preciso saber quanto
o resultado depende deles.

## O que fazer

Varredura, sempre no protocolo por participante e sem sobreposição:

| parâmetro | valores |
|---|---|
| janela do Hampel | 3, 7, 15 |
| janela da média móvel | 1 (sem), 5, 11 |

Seguir o modelo de `varredura_duracao.py`.

## Concluído quando

- [ ] Resultados em `.csv`, versionados
- [ ] Registro no `DIARIO.md`
- [ ] Se algum valor for claramente melhor, decisão registrada no `DECISOES.md`
