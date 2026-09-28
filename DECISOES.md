# Decisões de reprodução

Parâmetros e escolhas que os artigos originais não documentam, e que portanto
precisaram ser definidos neste trabalho. Cada divergência entre os resultados
obtidos e os publicados deve ser interpretada à luz desta tabela.

Os valores efetivamente usados em cada execução ficam registrados em
`registro_execucao.json`, gerado automaticamente.

---

## Pré-processamento

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| Filtro de Hampel — janela | 7 amostras | Mencionam o filtro; não informam parâmetros | Valor usual na literatura de processamento de sinais |
| Filtro de Hampel — limiar | 3 desvios (escala MAD × 1,4826) | Não informam | Critério padrão de 3σ |
| Média móvel — janela | 5 amostras | Mencionam; não informam tamanho | Suavização leve, preservando a dinâmica respiratória |
| Ordem das operações | amplitude → Hampel → média móvel | Texto ambíguo: sugere filtrar antes de extrair a amplitude | Filtrar antes de extrair a amplitude não faz sentido físico |

---

## Subamostragem

| Parâmetro | Valor adotado | Justificativa |
|---|---|---|
| Fator | 4 (de ~35 Hz para ~8,7 Hz) | O DS2 foi coletado a 2000 pacotes/min (~33 Hz), mas os artigos descrevem ~8–9 Hz, correspondente ao DS1. A subamostragem aproxima a taxa do protocolo descrito e reduz o custo do DTW em cerca de 10× |

**Consequência a declarar no relatório:** os artigos descrevem o protocolo DS1;
o dataset disponibilizado é DS2. A subamostragem mitiga a diferença, mas não a
elimina.

---

## Dynamic Time Warping

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| Variante | DTW clássico, distância euclidiana | Citam Senin (2008) e CC-DTW | Implementação de referência da biblioteca `dtaidistance` |
| Restrição de banda | Sakoe-Chiba, largura 50 | Não informam | Compromisso entre fidelidade e custo; ver medições no `DIARIO.md` |
| Ajuste da banda | `max(50, \|len(a) − len(b)\| + 1)` | — | Banda menor que a diferença de comprimento impede o caminho de alcançar o fim |
| Tratamento de séries degeneradas | Recálculo em Python puro quando o resultado não é finito | — | Subportadoras nulas têm série constante, o que quebra a poda da implementação em C |
| Normalização das séries | Nenhuma | Não mencionam | Ausência de menção tratada como ausência de normalização |

---

## Subportadoras

| Parâmetro | Valor adotado | Justificativa |
|---|---|---|
| Quantidade | 234 de 256 | Número informado nos artigos |
| Critério | Estrutura do padrão IEEE 802.11ac para 80 MHz | Guardas (6 + 5), DC (3) e pilotos (8) somam 22 descartadas, resultando exatamente em 234 |

Índices descartados (array de 0 a 255):
`0–5, 25, 53, 89, 117, 127, 128, 129, 139, 167, 203, 231, 251–255`

**Ressalva:** 4 subportadoras dentro da máscara (125, 126, 130, 131) aparecem
como constantes na saída do Nexmon. Foram mantidas para preservar o número 234
dos artigos; como são constantes, contribuem com features de baixa variância.

---

## Construção do conjunto de dados

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| Classe 1 (ocupada) | Posições 1 a 17, um segmento central por gravação | 17 posições por participante | Direto |
| Classe 0 (vazia) | Posição 0, 17 segmentos consecutivos por gravação | 1700 instâncias | Inferência — ver abaixo |
| **Comprimento das séries** | **Uniforme entre as classes: 29 amostras (~3,3 s)** | Não informam | **Obrigatório — ver abaixo** |
| Posição do segmento nas gravações ocupadas | Central | Não informam | Evita o transiente do início da gravação |
| Referência de sala vazia | Primeira gravação de posição 0 encontrada, segmento central | "escolhida aleatoriamente" | Escolha determinística, para reprodutibilidade |

**Comprimento uniforme — decisão obrigatória, não opcional.** A distância DTW
cresce com o comprimento das séries comparadas. Usar a gravação inteira para uma
classe e segmentos para a outra introduz diferença sistemática de escala entre
as classes, que os classificadores exploram como atalho. Isso ocorreu na
primeira execução e produziu desempenho artificialmente alto, inclusive no teste
com participantes nunca vistos. Ver `DIARIO.md`, entrada de 2026-09-23.

**Inferência principal a declarar:** o artigo relata 1700 instâncias de sala
vazia, mas existe apenas uma gravação de posição 0 por participante. A
segmentação de cada gravação em 17 trechos é a interpretação que reproduz o
número relatado; os artigos não a descrevem.

**Limitação decorrente:** a fragmentação reduz as séries de ~57 s para ~3,3 s.
O LATINCOM menciona uma coleta contínua de 6 horas de sala vazia, sugerindo que
os autores dispunham de gravações longas o bastante para extrair trechos de 60 s
sem fragmentar. O DS2 não oferece isso.

---

## Classificação

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| SVM | `SVC(kernel='linear')` com `StandardScaler` | Kernel linear | O SMO do Weka padroniza os dados de treino por padrão |
| J48 | `DecisionTreeClassifier(criterion='entropy', max_depth=3)` | J48, entropia, profundidade 3 | J48 é a implementação Weka do C4.5; a equivalência em scikit-learn é aproximada, não idêntica |
| Naive Bayes | `GaussianNB` com `StandardScaler` | NB sem prior | Variante gaussiana, adequada a atributos contínuos |
| Random Forest | `RandomForestClassifier(n_estimators=100)` | 100 estimadores | Direto |
| Divisão treino/teste | 70/30, estratificada | 70/30 | Estratificação preserva a proporção entre classes |
| Semente aleatória | 42 | Não informam | Valor fixo, para reprodutibilidade |

**Substituição a declarar:** J48 (Weka/C4.5) foi substituído por
`DecisionTreeClassifier` com critério de entropia. Os algoritmos diferem no
tratamento de poda e de atributos contínuos; divergências neste classificador
podem ter essa origem.

---

## Seleção de atributos

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| Método | `SelectKBest` com `f_classif` (ANOVA F) | "funções de regressão" | Expressão ambígua para um problema de classificação; ANOVA F é o critério padrão |
| Valores de k | 5, 10, 20, 50, 100, 234 | Curva na Figura 3 | Cobre a faixa relatada |

---

## Teste com participantes não vistos

| Parâmetro | Valor adotado | O que os artigos dizem | Justificativa |
|---|---|---|---|
| Quantidade | 18 participantes | 18 | Direto |
| Seleção | 18 maiores identificadores | Não informam quais | Critério determinístico |

**Limitação a declarar:** a composição do conjunto de teste quase certamente
difere da usada pelos autores. A Tabela 4 é, por isso, a menos provável de
reproduzir exatamente. A magnitude da queda de desempenho é mais informativa que
o valor absoluto.

---

## Instâncias descartadas

| Situação | Tratamento |
|---|---|
| Valor não finito em alguma feature | Instância descartada, com registro da quantidade e do percentual |

A quantidade descartada em cada execução consta no `registro_execucao.json`.
