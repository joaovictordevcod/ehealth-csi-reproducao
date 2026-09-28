---
titulo: 06 · Variante de DTW e normalização das séries
fase: Fase 1 — Investigação
labels: investigação
---

## Contexto

O LATINCOM cita Senin (2008) e CC-DTW, sem detalhar a variante nem a
normalização. Hoje usamos DTW clássico, banda de Sakoe-Chiba de 50 e nenhuma
normalização das séries.

## O que fazer

No protocolo por participante, sem sobreposição:

| variação | valores |
|---|---|
| largura da banda | 10, 50, sem restrição |
| normalização das séries antes do DTW | nenhuma, z-score |

A z-normalização remove diferenças de nível absoluto entre gravações — o que
pode reduzir o efeito de deriva, se ela existir ({02}).

## Concluído quando

- [ ] Resultados em `.csv`, versionados
- [ ] Registro no `DIARIO.md`
