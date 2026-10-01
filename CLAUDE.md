# Contexto do projeto

Reprodução independente do experimento de detecção de presença humana por Wi-Fi
CSI da Seção VII do artigo **eHealth CSI** (Galdino et al., IEEE Access 2023).
O método detalhado vem do artigo do **LATINCOM 2022** (Soto et al.), do mesmo
grupo. Trabalho de produção científica para a disciplina de Inteligência
Artificial Aplicada a Redes Sem Fio e Móveis (UFG).

**Antes de qualquer coisa, leia `DIARIO.md` e `DECISOES.md`.** Eles contêm o
histórico completo de decisões, os resultados já obtidos, os problemas já
enfrentados e as correções já aplicadas. Não refaça análises que já estão
registradas ali.

**O que falta fazer está no mapa do GitHub** (issue com label `wayfinder:map`)
e nas sub-issues dele. Glossário em `CONTEXT.md`.

---

## O que é e o que não é

**É:** reimplementação do pipeline descrito nos artigos, comparação numérica com
as tabelas publicadas, e registro explícito de toda decisão que os artigos não
documentam.

**Não é:** coleta nova de dados, método novo, nem crítica ao trabalho original.

O valor do trabalho não depende de os números baterem. Se divergirem, o
resultado é o mapeamento de quais decisões não documentadas mais afetam o
desempenho — e isso também é publicável.

---

## Estado atual

- Pipeline completo, corrigido e executado.
- **Tabela 3 (divisão aleatória):** só reproduz com janelas sobrepostas, e a
  varredura mostrou que esse ganho é vazamento. Sem sobreposição, RF ~87%.
- **Tabela 4 (participantes não vistos):** não reproduz. Generalização real
  entre 54% e 64% em qualquer duração, contra 76–91% publicados.
- A escolha dos 18 participantes de teste **não** explica a diferença.
- Os primeiros 18 participantes vão melhor que os demais, o que sugere deriva
  do ambiente ao longo da coleta.

- **As gravações do DS2 são de out/2023 em diante, posteriores ao IEEE Access
  (jul/2023).** O trabalho é uma *replicação* do método no DS2, não reprodução.
- Alvo único: Tabelas 3 e 4 da Seção VII do IEEE Access.

**Próximo passo:** ver a frente de trabalho do mapa no GitHub.

---

## Fatos do projeto que não estão nos artigos

Detalhamento em `DIARIO.md`.

- **O dataset é o DS2** (2000 pacotes/min, ~33 Hz), mas os artigos descrevem o
  protocolo **DS1** (500 pacotes/min, ~8,3 Hz). O pipeline subamostra por 4.
- **Sala vazia é a posição `00`**, uma gravação por participante.
- **100 participantes** têm posição 0 e todas as posições 1–17.
  100 × 17 = 1700, o número de instâncias do artigo.
- **Máscara de subportadoras vem do padrão 802.11ac**: guardas (6+5) + DC (3) +
  pilotos (8) = 22 descartadas → 234.
- **O DTW quebra em séries constantes.** Subportadoras nulas do Nexmon são
  constantes. Solução: recalcular em Python puro quando o resultado não é
  finito. **Não use `use_pruning=False`** — produz lixo numérico (~1e300).
- **SVM e NB precisam de `StandardScaler`.** O SMO do Weka já padroniza.
- **As duas classes precisam ter séries do mesmo comprimento.** O DTW cresce com
  o comprimento; comprimentos diferentes viram atalho para o classificador.
- **Janelas sobrepostas invalidam a divisão aleatória.** Só o protocolo por
  participante é interpretável com sobreposição.

---

## Questões em aberto para o grupo responsável pelo dataset

1. O DS1 está disponível?
2. Os 18 participantes da Tabela 4 — de onde vêm? O artigo menciona 118
   participantes; o `valid.txt` do DS2 lista 106, dos quais 100 completos.
3. A coleta contínua de 6 horas de sala vazia citada no LATINCOM está
   disponível? Foi usada no IEEE Access?
4. Como foram obtidas as 1700 instâncias de sala vazia?

---

## Convenções

- **Documentar é parte do trabalho.** Toda decisão nova vai para `DECISOES.md`;
  todo passo, resultado ou problema vai para `DIARIO.md`. Atualize antes de
  commitar, não depois.
- **Nunca versionar dados.** `.npz` e o dataset ficam fora do git. Resultados
  em `.csv` e `.json` são versionados.
- Parâmetros ficam centralizados em `PARAMS`, em `csi_pipeline.py`.
- Idioma do projeto: português.

---

## Ambiente

O ambiente virtual fica **fora** do repositório:

```bash
python3 -m venv ~/venv-csi
~/venv-csi/bin/pip install numpy pandas scipy scikit-learn dtaidistance datasette
```

Dataset, não versionado:

```
~/Downloads/eHealth/Data_DS2_raspberry_npz/NNN/PP_AAAA_MM_DD_-_HH_MM_SS_bw_80_ch_36.npz
```
