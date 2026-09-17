# Códigos de posição — eHealth CSI

Conforme `README_eHealth.md` do dataset. O código é o prefixo do nome do arquivo.

| Código | Posição | Respiração |
|---|---|---|
| 00 | Ausência de pessoa (sala vazia) | — |
| 01 | Sentado de frente | normal |
| 02 | Sentado de frente | intermitente |
| 03 | Senta e levanta (a cada 10 s) | normal |
| 04 | Sentado de costas | normal |
| 05 | Sentado de costas | intermitente |
| 06 | Em pé, de frente | normal |
| 07 | Em pé, de frente | intermitente |
| 08 | Em pé, de costas | normal |
| 09 | Em pé, de costas | intermitente |
| 10 | Deitado de barriga para cima | normal |
| 11 | Deitado de barriga para cima | intermitente |
| 12 | Deitado de bruços | normal |
| 13 | Deitado de bruços | intermitente |
| 14 | Deita e levanta (a cada 20 s) | normal |
| 15 | Caminhando | normal |
| 16 | Correndo | normal |
| 17 | Varrendo | normal |
| 18 | Em pé e queda (20 s e 40 s) | normal |

**Respiração normal:** respiração natural durante todo o minuto de gravação.

**Respiração intermitente:** 20 s respirando, 10 s em apneia, repetindo até
completar o minuto.

---

## Estrutura do nome do arquivo

```
17_2023_10_30_-_12_45_27_bw_80_ch_36.npz
│  │                     │     │
│  │                     │     └─ canal 36
│  │                     └─────── largura de banda 80 MHz
│  └───────────────────────────── início da captura
└──────────────────────────────── código da posição
```

O identificador do participante é o nome da pasta que contém o arquivo.

---

## Protocolos de coleta

| | Pacotes/min | Taxa efetiva | Posições coletadas |
|---|---|---|---|
| DS1 | 500 | ~8,3 Hz | 1 a 17 |
| DS2 | 2000 | ~33 Hz | 1 a 18 |

Este trabalho usa o **DS2**.

---

## Integridade

O arquivo `valid.txt` do dataset marca, por participante e posição, `o` para
coleta íntegra e `m` para coleta ausente.

Resumo do DS2:

- 106 participantes listados
- posição 0 ausente em 3 participantes (7, 8, 87)
- posições 1–17 incompletas em 3 participantes (81, 85, 90)
- posição 18 disponível apenas a partir do participante 66
- **100 participantes com posição 0 e todas as posições 1–17**
