# Replicação — detecção de presença por Wi-Fi CSI

Glossário do projeto que aplica o método de detecção de presença do grupo
MidiaCom (LATINCOM 2022, Seção IV) ao dataset eHealth CSI e compara os números
com os publicados na Seção VII do IEEE Access 2023.

## Natureza do trabalho

**Replicação**:
Aplicar o método publicado a um dado diferente do usado pelos autores, que aqui
é o DS2. É o que este trabalho faz.
_Evitar_: reprodução (exceto se o DS1 for obtido)

**Reprodução**:
Aplicar o método publicado ao mesmo dado usado pelos autores. Só é possível com
o DS1.

**Alvo**:
Tabelas 3 e 4 do IEEE Access 2023, Seção VII. O LATINCOM 2022 é só fonte do
método, não de números a comparar.

## Dados

**DS1**:
Protocolo de coleta a 500 pacotes/min (~8,3 Hz), com posições 1–17, coletado
antes de jul/2023. É o dado dos dois artigos. Não está disponível para nós.

**DS2**:
Protocolo de coleta a 2000 pacotes/min (~33 Hz), com posições 0–18, coletado a
partir de out/2023, depois dos dois artigos. É o dado que temos.

**Gravação**:
Um arquivo `.npz` de ~60 s de um participante numa posição.
_Evitar_: coleta, captura, arquivo

**Sala vazia**:
Gravação da posição `00`, feita no início de cada sessão, antes das posições
com o participante.
_Evitar_: empty room, ausência

**Sala ocupada**:
Gravação de qualquer posição de 1 a 17 com o participante presente.
_Evitar_: filled room

**Referência**:
O trecho de sala vazia contra o qual todas as instâncias são comparadas por
DTW.

## Construção do conjunto

**Segmento**:
Trecho contíguo de uma gravação, com comprimento fixo em amostras, usado como
série de entrada do DTW.
_Evitar_: janela (reservado para os filtros)

**Sobreposição**:
Fração compartilhada entre segmentos consecutivos de uma mesma gravação de sala
vazia.

**Instância**:
Um vetor de 234 distâncias DTW (uma por subportadora) entre um segmento e a
referência.

## Avaliação

**Divisão aleatória**:
Protocolo 70/30 estratificado sobre instâncias, sem considerar o participante.
Corresponde à Tabela 3.

**Participantes não vistos**:
Protocolo em que todas as instâncias de 18 participantes ficam fora do treino.
Corresponde à Tabela 4.
_Evitar_: holdout, teste (sem qualificação)

**Vazamento**:
Ganho de acurácia vindo de instâncias quase duplicadas que caem em treino e
teste ao mesmo tempo.

**Deriva**:
Mudança do ambiente ao longo do tempo que afasta a sala vazia da referência,
seja entre sessões (entre participantes) ou dentro da mesma sessão (entre
posições).
