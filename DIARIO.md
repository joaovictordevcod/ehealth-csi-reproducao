# Diário de pesquisa

Registro cronológico do trabalho. Cada entrada documenta o que foi feito, o que
foi descoberto e o que foi decidido — incluindo o que deu errado.

---

## Definição do tema

**Decisão:** reproduzir o experimento de detecção de presença humana por Wi-Fi CSI
publicado pelo grupo MidiaCom/UFF.

O recorte inicial era reproduzir o artigo do LATINCOM 2022 (25 participantes,
850 instâncias). Essa escolha foi revista depois — ver entrada
*Descoberta: DS1 vs DS2*.

**Justificativa do tipo de trabalho:** reprodutibilidade é um problema
reconhecido em sensoriamento Wi-Fi, e refazer um trabalho publicado é exercício
raro. O valor do trabalho não depende de os números baterem: se divergirem,
o resultado é o mapeamento de quais decisões não documentadas mais afetam o
desempenho.

---

## Levantamento dos artigos

Identificados dois artigos do mesmo grupo, com papéis diferentes:

- **LATINCOM 2022** — descreve o método em detalhe (pipeline, pré-processamento,
  DTW, classificadores, seleção de atributos).
- **IEEE Access 2023** — artigo de dataset. A detecção de presença aparece na
  Seção VII como exemplo de aplicação, resumida em pouco mais de uma página.

**Consequência:** o método vem do LATINCOM; os números-alvo, do IEEE Access.

### Lacunas identificadas nos artigos

Nenhum dos dois documenta:

1. janela e limiar do filtro de Hampel;
2. tamanho da janela da média móvel;
3. variante de DTW, restrição de banda e normalização;
4. função de pontuação usada na seleção de atributos;
5. ordem exata do pré-processamento (o texto é ambíguo sobre amplitude e filtros);
6. semente aleatória e composição exata do conjunto de teste;
7. como 1700 instâncias de sala vazia foram obtidas a partir de ~100 gravações.

Todas essas decisões estão registradas em `DECISOES.md`.

### Divergência entre os dois artigos

O LATINCOM informa 9 amostras por segundo. O IEEE Access descreve intervalo de
transmissão de 136 ms, o que corresponderia a ~7,35 Hz. A medição no dado real
resolveu essa divergência — ver entrada seguinte.

---

## 2026-09-16 — Primeiro contato com o dado

Analisado um arquivo `.npz` isolado (participante não identificado, posição 17).

### Estrutura do arquivo

```
csi       (2000, 256)   complex64   CSI bruto por pacote × subportadora
ts        (2000,)       float64     timestamp por pacote (epoch Unix)
metadata  (2001,)       object      [0] resumo do arquivo, [1:] um dict por pacote
```

Campos do metadata por pacote: `frame_index`, `timestamp_sec`, `src_mac`,
`sequence`, `core`, `spatial_stream`, `chanspec`, `chip_version`,
`bandwidth_mhz`, `nfft`.

Confirmado: antena única (`core=0`, `spatial_stream=0`), 80 MHz, FFT de 256.

### Medições

- 2000 pacotes em 57,3 s → **~35 pacotes/s**
- intervalo médio entre pacotes: 28,7 ms (desvio-padrão 5,3 ms)
- nenhum NaN ou infinito no CSI bruto
- tamanho: 1,75 MB por arquivo

### Observação registrada

O perfil de amplitude média por subportadora mostra um pico agudo nos índices
126–131 (valores de 400 a 8200, contra mediana global de 34,6) e um platô
elevado de ~132 a 189. O pico é a região de DC; o platô é dado real com ganho
mais alto, provável artefato de ganho por segmento de 20 MHz.

---

## 2026-09-17 — Documentação oficial do dataset

Recebidos do responsável pelo dataset: `README_eHealth.md`, `README_DS2.md`,
`valid.txt`, `specs_devices.txt` e um documento de orientações iniciais.

### Três questões resolvidas

**1. Sala vazia é a posição `00`.** O README lista os códigos de posição, e
`00 - Absence of a person`. Cada participante tem um arquivo dessa posição.
Isso define a classe negativa do experimento.

**2. A taxa de amostragem — divergência explicada.** O README separa dois
protocolos de coleta:

| | Pacotes/min | Equivale a | Posições |
|---|---|---|---|
| DS1 | 500 | ~8,3 Hz | 1–17 |
| DS2 | 2000 | ~33 Hz | 1–18 |

A medição de ~35 Hz corresponde ao DS2. Os "9 amostras por segundo" do LATINCOM
correspondem ao DS1.

**3. O arquivo analisado era posição 17** — "varrer, respiração normal". Explica
a alta variabilidade observada no heatmap.

### Integridade — análise do valid.txt

106 participantes listados no DS2. Marcação `o` (coletado) / `m` (faltante) por
posição.

- posição 0 (sala vazia) disponível para 103 participantes; faltante em 7, 8 e 87;
- posições 1–17 completas em 103 participantes; incompletas em 81, 85 e 90;
- posição 18 disponível apenas a partir do participante 66;
- **participantes com posição 0 e todas as posições 1–17: exatamente 100.**

100 × 17 = **1700 instâncias de sala ocupada** — o número exato relatado na
Seção VII do IEEE Access.

---

## Descoberta: DS1 vs DS2 — mudança de escopo

**Problema:** o LATINCOM (artigo-alvo inicial) usou DS1 — 25 participantes,
~9 Hz. O dataset disponibilizado é DS2 — 106 participantes, ~33 Hz.

Taxa de amostragem 4× maior altera o comprimento das séries que entram no DTW
e, muito provavelmente, os números finais.

**Alternativas consideradas:**

| | Descrição | Avaliação |
|---|---|---|
| A | Solicitar o DS1 e reproduzir o LATINCOM | Depende de disponibilidade e de nova espera |
| B | Mudar o alvo para o IEEE Access, Seção VII | Os dados correspondem exatamente ao experimento |
| C | Amostrar 25 participantes do DS2 | Escala aproximada, mas taxa diferente; números não bateriam e não se saberia por quê |

**Decisão: opção B.** O método continua vindo do LATINCOM; as tabelas-alvo
passam a ser as do IEEE Access. O contraste entre o protocolo descrito nos
artigos (DS1) e o dataset publicado (DS2) passa a constar no relatório.

### Questões em aberto para o grupo responsável

1. O DS1 está disponível?
2. Os 18 participantes do teste da Tabela 4 — de onde vêm? O artigo menciona 118
   participantes, o `valid.txt` do DS2 lista 106, dos quais 100 completos.
   A conta não fecha.

---

## Máscara de subportadoras

**Problema:** os artigos usam 234 subportadoras; os arquivos têm 256.
Quais 22 descartar?

**Primeira tentativa (descartada):** identificar empiricamente as subportadoras
com amplitude média muito acima da mediana. A heurística selecionou os índices
145–162, que são subportadoras de dados com ganho mais alto — não nulas.
Apenas 2 dos 22 índices coincidiam com o padrão.

**Solução adotada:** usar a estrutura do padrão IEEE 802.11ac para 80 MHz com
FFT de 256 pontos (índices lógicos −128 a +127, índice do array = lógico + 128):

| Componente | Índices lógicos | Quantidade |
|---|---|---|
| guarda à esquerda | −128 a −123 | 6 |
| guarda à direita | +123 a +127 | 5 |
| DC | −1, 0, +1 | 3 |
| pilotos | ±11, ±39, ±75, ±103 | 8 |
| | **total descartado** | **22** |

256 − 22 = **234 subportadoras de dados**, coincidindo com o número dos artigos.

**Validação empírica:** os índices de DC (127, 128, 129) apresentam amplitude
média de 1608, 3257 e 397 contra mediana global de 34,6 — cerca de 50× acima,
confirmando a estrutura.

---

## Custo computacional do DTW

Medido com dados reais antes de investir na implementação completa, por ser o
risco técnico principal do projeto.

Série de 2000 amostras, uma comparação:

| Configuração | Tempo/par | Extrapolado (3400 × 234 pares) |
|---|---|---|
| sem restrição de banda | 10,66 ms | 2,35 h |
| banda = 100 | 1,80 ms | — |
| banda = 50 | 0,81 ms | — |
| subamostrado 1/4, banda = 50 | 0,21 ms | **3 min** |

**Decisão: subamostrar por 4.** Além de reduzir o custo em ~10×, leva o DS2 de
~33 Hz para ~8,7 Hz — aproximadamente a taxa do DS1, que é o protocolo descrito
nos artigos. A decisão se justifica em duas frentes.

---

## Problemas encontrados na execução

Registrados porque cada um exigiu uma decisão que afeta o resultado.

### Problema 1 — DTW retornando infinito por diferença de comprimento

**Sintoma:** `ValueError: Input X contains infinity`.

**Causa:** com restrição de banda de Sakoe-Chiba, se a diferença de comprimento
entre as duas séries excede a largura da banda, o caminho não alcança o fim e o
DTW retorna infinito.

**Correção:** largura efetiva da banda passou a ser
`max(banda_configurada, |len(a) − len(b)| + 1)`.

**Resultado:** correção necessária, mas insuficiente — o erro persistiu.

### Problema 2 — DTW retornando infinito em séries constantes

**Diagnóstico:** 2184 de 3510 instâncias afetadas, exatamente 1 feature por
instância. Rastreado até a subportadora 130, cuja série é **constante** — todos
os 500 valores iguais a 3031,047607421875.

Verificação no arquivo completo: **8 subportadoras constantes**, índices
1, 125, 126, 127, 128, 129, 130, 131 — a região de DC, que o Nexmon preenche
com valor fixo.

A implementação em C do `dtaidistance` usa poda baseada em limite superior, que
é degenerada para séries constantes, e retorna infinito.

### Problema 3 — desligar a poda produz lixo numérico

**Tentativa:** usar `use_pruning=False`.

**Resultado:** o número de instâncias afetadas caiu de 2184 para 54, mas
apareceram valores da ordem de 1e223 a 1e308 espalhados por quase todas as
colunas — enquanto a mediana das features é 5,0 e o percentil 99 é 1431.
São valores sem significado, provavelmente memória não inicializada.

**Descartado.**

### Problema 4 — SVM não converge sem padronização

**Sintoma:** `The dual coefficients or intercepts are not finite`.

**Causa:** as distâncias DTW têm faixa dinâmica muito larga para um SVM linear
sem padronização.

**Correção:** `StandardScaler` antes de SVM e Naive Bayes. Justificativa
adicional: o SMO do Weka — usado pelos autores originais — padroniza os dados de
treino por padrão, de modo que a inclusão aproxima o comportamento do original.
Árvores e florestas são invariantes a escala; não foram alteradas.

### Solução adotada para o DTW

Poda **ligada** (comportamento padrão, bem testado) com verificação do resultado:
quando o valor retornado não é finito, recalcula com a implementação em Python
puro, que é robusta a séries degeneradas.

Validação em 256 subportadoras entre dois trechos distintos: zero valores não
finitos, zero recálculos necessários, 21 ms por instância.

---

## 2026-09-23 — Primeira execução completa

Pipeline rodou do início ao fim: 106 participantes, 3510 instâncias,
X = (3510, 234).

### Tabela 3 — reproduziu

| | obtido | publicado | diferença |
|---|---|---|---|
| SVM | 99,81 | 99,90 | −0,09 |
| RF | 100,00 | 99,90 | +0,10 |
| NB | 94,40 | 93,43 | +0,97 |
| J48 | 99,91 | 94,90 | +5,01 |

Três dos quatro classificadores dentro de 1 ponto percentual. A divergência do
J48 é atribuível à substituição do C4.5 do Weka por `DecisionTreeClassifier`,
registrada em `DECISOES.md`.

### Tabela 4 — não reproduziu, e na direção errada

| | obtido | publicado | diferença |
|---|---|---|---|
| SVM | 99,16 | 76,47 | +22,69 |
| J48 | 98,99 | 78,92 | +20,07 |
| NB | 97,15 | 83,33 | +13,82 |
| RF | 99,33 | 91,18 | +8,15 |

Desempenho **muito superior** ao publicado em teste com participantes nunca
vistos. O teste de holdout existe para o desempenho cair — no artigo cai de
99,90 para 91,18. Aqui não caiu. Resultado bom demais em holdout é indício de
vazamento, não de sucesso.

### Diagnóstico — artefato de comprimento entre as classes

**Causa identificada:** as duas classes usavam séries de comprimentos
diferentes.

- classe 1 (ocupada): gravação inteira, ~500 amostras
- classe 0 (vazia): segmento, ~29 amostras

A distância DTW cresce com o comprimento das séries comparadas. As features
ficaram com escalas sistematicamente diferentes entre as classes, e os
classificadores exploravam essa diferença como atalho — um atalho independente
do participante, o que explica o holdout não degradar.

**Verificação:**

| | mediana das features |
|---|---|
| classe 1 (ocupada) | 209,37 |
| classe 0 (vazia) | 70,57 |
| razão | 3,0 |

O escalonamento esperado do DTW, que cresce com a raiz do comprimento, seria
√(500/29) ≈ 4,2. A razão observada é da mesma ordem, confirmando que o artefato
é real. Parte da razão pode ser sinal genuíno — sala ocupada de fato difere mais
da referência vazia do que outra sala vazia — mas não há como separar as duas
contribuições sem corrigir o comprimento.

**Correção adotada:** todas as instâncias, das duas classes, passam a usar
segmentos do mesmo comprimento.

- comprimento do segmento: `len(gravação) // n_empty_segments` = 29 amostras
- classe 1: um segmento central por gravação → 100 × 17 = 1700
- classe 0: 17 segmentos consecutivos por gravação → 100 × 17 = 1700
- referência: segmento central da gravação de referência

O segmento central foi escolhido em vez do inicial para evitar o transiente do
começo da gravação, em que o participante ainda se acomoda na posição.

**Limitação a declarar no relatório:** com o DS2 não existem 1700 gravações
independentes de sala vazia de 60 s — há uma por participante. Obter 1700
instâncias exige fragmentar as gravações, o que reduz o comprimento das séries
de ~57 s para ~3,3 s. O LATINCOM menciona uma coleta contínua de 6 horas de
sala vazia, o que sugere que os autores dispunham de gravações longas o
bastante para extrair trechos de 60 s sem fragmentação. Essa diferença entre o
dado descrito e o dado disponível é um achado do trabalho.

---

## 2026-09-23 — Execução com comprimento uniforme (29 amostras)

Reexecução com segmentos de 29 amostras (~3,3 s) nas duas classes.

| | aleatório 70/30 | participantes não vistos | publicado (T3 / T4) |
|---|---|---|---|
| SVM | 65,53 | 59,06 | 99,90 / 76,47 |
| J48 | 63,63 | 55,54 | 94,90 / 78,92 |
| NB | 48,62 | 53,86 | 93,43 / 83,33 |
| RF | 88,13 | 56,21 | 99,90 / 91,18 |

**O atalho sumiu:** o teste com participantes não vistos agora degrada em
relação à divisão aleatória, como esperado.

**Mas o desempenho caiu muito abaixo do publicado.** O NB chega a 48,62% com
recall de 2,25% — classifica quase tudo como sala vazia.

**Hipótese:** a correção igualou os comprimentos por baixo, reduzindo a classe 1
de 57 s para 3,3 s e descartando 94% de cada gravação ocupada. O RF ainda
encontra 88% de sinal, indicando que há informação, mas pouca.

---

## 2026-09-23 — Varredura da duração do segmento

Script: `varredura_duracao.py`. Testa cinco durações, nos dois protocolos.

Para obter 1700 instâncias de sala vazia com segmentos longos, as janelas da
posição 0 precisam se sobrepor. A sobreposição cresce com a duração.

### Random Forest

| duração | sobreposição | aleatório 70/30 | não vistos | queda |
|---|---|---|---|---|
| 3,3 s | 0% | 86,80 | 59,23 | 27,6 |
| 6,9 s | 55% | 90,88 | 57,05 | 33,8 |
| 14,3 s | 82% | 94,21 | 55,20 | 39,0 |
| 28,7 s | 94% | 96,30 | 55,70 | 40,6 |
| 45,8 s | 98% | 98,29 | 54,19 | 44,1 |

### Todos os classificadores — participantes não vistos

| duração | SVM | J48 | NB | RF |
|---|---|---|---|---|
| 3,3 s | 59,23 | 56,21 | 53,36 | 59,23 |
| 6,9 s | 58,05 | 58,72 | 54,03 | 57,05 |
| 14,3 s | 60,07 | 55,87 | 50,67 | 55,20 |
| 28,7 s | 59,73 | 57,21 | 50,17 | 55,70 |
| 45,8 s | 63,93 | 57,38 | 48,15 | 54,19 |

### Conclusão — o ganho com duração é vazamento, não sinal

Na divisão aleatória o RF sobe até 98,29%, quase o valor publicado. No teste com
participantes não vistos ele **não sobe** — cai levemente — e a queda entre os
dois protocolos cresce de 27 para 44 pontos.

A queda acompanha a sobreposição das janelas de sala vazia. Janelas sobrepostas
de um mesmo participante são quase duplicatas; na divisão aleatória elas caem
em treino e teste ao mesmo tempo, e o teste deixa de medir generalização. No
protocolo por participante isso não ocorre, porque o participante inteiro sai
do treino.

**O desempenho real de generalização no DS2 fica entre 54% e 64%,
independentemente da duração.** O publicado na Tabela 4 é 76–91%.

**Implicação a verificar, sem afirmar:** se os autores também fragmentaram
gravações curtas de sala vazia com sobreposição, a Tabela 3 deles estaria
sujeita ao mesmo efeito. O LATINCOM menciona uma coleta contínua de 6 horas,
o que sugere que eles tinham material para não precisar sobrepor. É uma
pergunta para o grupo responsável, não uma conclusão.

---

## 2026-09-28 — A escolha dos 18 participantes explica a diferença?

Script: `teste_holdout.py`, sobre as features de 29 amostras (sem sobreposição).

**Motivação:** o holdout usava os 18 maiores identificadores. Os IDs são
sequenciais por ordem de coleta, então isso testava nos participantes coletados
por último — os mais distantes no tempo da referência de sala vazia
(participante 001).

| cenário | SVM | J48 | NB | RF |
|---|---|---|---|---|
| últimos 18 | 59,23 | 56,21 | 53,36 | 59,23 |
| **primeiros 18** | 66,84 | 64,71 | 45,81 | **68,81** |
| sorteados — média (20×) | 59,18 | 60,80 | 49,18 | 59,74 |
| sorteados — desvio-padrão | 2,48 | 3,01 | 3,17 | 3,20 |
| sorteados — máximo | 64,14 | 64,87 | 58,82 | 64,87 |
| publicado (Tabela 4) | 76,47 | 78,92 | 83,33 | 91,18 |

**A escolha do holdout não explica a diferença.** Sortear os 18 dá praticamente
o mesmo que usar os últimos — 59,74 contra 59,23 no RF.

**Mas os primeiros 18 destoam.** RF a 68,81%, quase 3 desvios-padrão acima da
média dos sorteios e acima do máximo em 20 repetições. Não é ruído.

Os primeiros participantes são contemporâneos da referência de sala vazia. Isso
é consistente com **deriva do ambiente ao longo da coleta**: se a sala mudou
nos meses de coleta, a distância até uma referência antiga cresce, e salas
vazias tardias passam a parecer ocupadas.

Mesmo no melhor caso, o resultado fica 22 pontos abaixo do publicado. A deriva
explicaria parte da diferença, não toda.

### Próximo passo

Medir diretamente a deriva: `teste_deriva.py` verifica se a distância das
gravações de sala vazia até a referência cresce com o número do participante.

---

## 2026-10-01 — Datas do DS2 e redefinição do escopo

**Descoberta:** as gravações do DS2 têm datas de 30/10/2023 (participante 001)
e 08/11/2023 (exemplo do `README_DS2.md`). O IEEE Access foi recebido em
02/06/2023 e publicado em 11/07/2023. Portanto **a Seção VII não pode ter usado
o DS2** — quase certamente usou o DS1 (500 pacotes/min, posições 1–17, 118
participantes). A coincidência 100 × 17 = 1700 que motivou a opção B da entrada
*Descoberta: DS1 vs DS2* não prova correspondência. Verificação completa (datas
de todas as gravações) é um ticket do mapa.

**Observação:** no DS2 a sala vazia é gravada primeiro, e a ordem das posições é
1, 3, 4, 6, 8, 10, 12, 14, 2, 5, 7, 9, 11, 13, 15–18. Há possível deriva também
*dentro* da sessão.

**Decisões:**
- O trabalho passa a ser **replicação** do método no DS2, não reprodução.
- Alvo único: Tabelas 3 e 4 da Seção VII do IEEE Access. Resultados do
  LATINCOM (desbalanceado, seleção de atributos) saem do escopo.
- Configuração final segue o texto dos artigos; varreduras são análise de
  sensibilidade, e a melhor configuração encontrada (escolhida sem olhar o
  teste) entra como linha à parte.
- Nada depende de resposta do MidiaCom; o e-mail vai sem bloquear.
- Prazo desta fase: 12/10/2026.
- O roteiro passa ao mapa do GitHub (issue #1); `roteiro/` vira histórico.

**Datas do DS2 pela Polar H10** (gravada junto com o CSI; o CSI ainda não foi
copiado para esta máquina): 1673 gravações de 30/10/2023 a 09/10/2025 —
out/2023–jan/2024: 1003; jun/2024: 17; out/2024–jan/2025: 582;
jul–out/2025: 54. A coleta cobre ~2 anos; nenhuma sessão é anterior ao artigo.
Os 18 participantes de teste são de 2025; a referência é de out/2023.

**Protocolo de seleção da melhor configuração** definido — ver `DECISOES.md`,
seção *Seleção da melhor configuração encontrada*.

---

## Estado atual

- [x] Escopo definido e justificado
- [x] Dataset obtido, estrutura compreendida, integridade verificada
- [x] Máscara de subportadoras definida e validada
- [x] Custo do DTW medido
- [x] Pipeline implementado
- [x] Bugs numéricos do DTW diagnosticados e corrigidos
- [x] Execução completa
- [x] Artefato de comprimento entre classes identificado e corrigido
- [x] Varredura de duração — ganho com segmentos longos é vazamento
- [x] Teste de holdout — escolha dos 18 não explica a diferença
- [ ] **Teste de deriva temporal** — próximo
- [ ] Investigar a causa restante da diferença na Tabela 4
- [ ] Figuras para o relatório
- [ ] Redação do relatório

Acompanhamento detalhado nas issues do repositório.
