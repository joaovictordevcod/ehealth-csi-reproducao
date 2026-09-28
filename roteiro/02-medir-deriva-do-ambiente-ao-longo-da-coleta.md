---
titulo: 02 · Medir deriva do ambiente ao longo da coleta
fase: Fase 1 — Investigação
labels: investigação
---

## Contexto

No teste com participantes não vistos, os **primeiros 18** participantes
tiveram RF de 68,81%, contra 59,74% ± 3,20 nos sorteios — acima de toda a
faixa de 20 repetições. Os primeiros participantes são contemporâneos da
referência de sala vazia (participante 001).

Hipótese: a sala mudou ao longo dos meses de coleta, e a distância até uma
referência antiga cresce com o tempo, fazendo salas vazias tardias parecerem
ocupadas.

## O que fazer

```bash
~/venv-csi/bin/pip install scipy
~/venv-csi/bin/python teste_deriva.py features_seg29.npz
```

## Como ler

- Correlação de Spearman alta e positiva na classe **sala vazia** → deriva
  confirmada; seguir para {03}.
- Correlação próxima de zero → deriva descartada; a causa está em outro lugar
  ({04}, {05}, {06}).

## Concluído quando

- [ ] Resultado registrado no `DIARIO.md`, com a tabela e a interpretação
- [ ] `teste_deriva.csv` versionado
