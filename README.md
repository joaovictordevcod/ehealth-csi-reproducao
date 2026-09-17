# Reprodução — Detecção de presença humana por Wi-Fi CSI

Reprodução independente do experimento de detecção de presença publicado pelo
grupo MidiaCom (UFF), usando o dataset eHealth CSI.

Trabalho de produção científica — disciplina de Inteligência Artificial Aplicada
a Redes Sem Fio e Móveis, Universidade Federal de Goiás.

---

## Objetivo

Verificar se os resultados publicados podem ser obtidos por um terceiro, a partir
apenas do que está descrito nos artigos e do dataset disponibilizado.

O trabalho **é**:
- reimplementação independente do pipeline descrito nos artigos;
- comparação numérica com as tabelas publicadas;
- registro explícito de toda decisão que os artigos não documentam.

O trabalho **não é**:
- coleta nova de dados;
- proposta de método novo;
- crítica ao trabalho original.

---

## Artigos de referência

| | Referência | Papel neste trabalho |
|---|---|---|
| **Método** | Soto, J. C. H. et al. *Wi-Fi CSI-based Human Presence Detection Using DTW Features and Machine Learning.* IEEE LATINCOM, 2022. doi:10.1109/LATINCOM56090.2022.10000702 | Descrição detalhada do pipeline |
| **Dados e alvo** | Galdino, I. et al. *eHealth CSI: A Wi-Fi CSI Dataset of Human Activities.* IEEE Access 11:71003-71012, 2023. doi:10.1109/ACCESS.2023.3294429 | Dataset e tabelas a reproduzir |

### Números-alvo

Tabela 3 do IEEE Access — split 70/30, dados balanceados:

| | SVM | J48 | NB | RF |
|---|---|---|---|---|
| Acurácia (%) | 99,90 | 94,90 | 93,43 | 99,90 |

Tabela 4 do IEEE Access — 18 participantes nunca vistos no treino:

| | SVM | J48 | NB | RF |
|---|---|---|---|---|
| Acurácia (%) | 76,47 | 78,92 | 83,33 | 91,18 |

Figura 3 do LATINCOM — seleção de atributos: 5 features selecionadas atingem
99,98% com Random Forest; acima de 20 features a acurácia declina.

---

## Dados

Dataset **eHealth CSI, versão DS2** — Raspberry Pi 4B com firmware Nexmon,
5 GHz, canal 36, largura de banda 80 MHz.

Acesso sob solicitação a `csi@midiacom.uff.br`, mediante assinatura de Data
Usage Agreement. **Não versionado neste repositório.**

Estrutura esperada:

```
Data_DS2_raspberry_npz/
├── 001/
│   ├── 00_2023_10_30_-_12_18_26_bw_80_ch_36.npz   <- sala vazia
│   ├── 01_2023_10_30_-_12_20_05_bw_80_ch_36.npz
│   └── ...                                         (posições 00 a 18)
├── 002/
└── ...                                             (106 participantes)
```

Cada `.npz` contém três arrays: `csi` (n_pacotes × 256, complexo),
`ts` (timestamps) e `metadata` (resumo + um registro por pacote).

Códigos de posição em `docs/posicoes.md`.

---

## Estrutura do repositório

| Arquivo | Função |
|---|---|
| `csi_pipeline.py` | Leitura dos `.npz`, pré-processamento, extração de features por DTW |
| `run_experiment.py` | Classificadores, tabelas de resultado, comparação com os valores publicados |
| `analyze.py` | Roda a análise a partir de um `features.npz` já calculado |
| `build_catalog.py` | Indexa o dataset em SQLite para inspeção |
| `inspect_npz.py` | Diagnóstico de um arquivo `.npz` isolado, com figuras |
| `DIARIO.md` | Registro cronológico do trabalho — o que foi feito, o que quebrou, o que foi decidido |
| `DECISOES.md` | Parâmetros e escolhas que os artigos não documentam |

---

## Como executar

```bash
python3 -m venv venv
./venv/bin/pip install numpy pandas scikit-learn dtaidistance datasette

# 1. inspecionar o dataset
./venv/bin/python build_catalog.py /caminho/Data_DS2_raspberry_npz catalogo.db valid.txt
./venv/bin/datasette catalogo.db

# 2. rodar o experimento completo (calcula DTW, ~10 min)
./venv/bin/python run_experiment.py /caminho/Data_DS2_raspberry_npz

# 3. reanalisar sem recalcular DTW
./venv/bin/python analyze.py
```

Saídas: `features.npz` (matriz de features) e `registro_execucao.json`
(parâmetros e resultados de cada execução).

---

## Escopo

**Dentro:** pipeline completo do `.npz` à classificação; quatro classificadores;
dados balanceados e desbalanceados; seleção de atributos; teste com participantes
não vistos.

**Fora:** coleta de dados; reprodução do DS1; análise dos dados de Polar H10 e
smartwatch.

---

## Autores

João Victor Borges — Universidade Federal de Goiás
