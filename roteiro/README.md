# Roteiro

> **Histórico — substituído em 01/10/2026.** O roteiro de trabalho agora vive no
> mapa do GitHub: [Mapa: replicação da Seção VII do IEEE Access no DS2](https://github.com/joaovictordevcod/ehealth-csi-reproducao/issues/1).
> Estas fichas ficam só como registro; não crie issues a partir delas.

Cada arquivo `NN-*.md` desta pasta é uma issue do repositório. O número no nome
define a ordem em que devem ser feitas.

As issues são criadas no GitHub pelo workflow **Criar issues do roteiro**
(aba Actions → Run workflow), que executa `criar_issues.py`.

---

## Formato

```markdown
---
titulo: 07 · Rodar o cenário desbalanceado
fase: Fase 2 — Consolidação
labels: investigação
---

## Contexto

Texto em markdown...
```

| Campo | Valores aceitos |
|---|---|
| `titulo` | Livre. Por convenção começa com o número do arquivo. |
| `fase` | `Fase 1 — Investigação`, `Fase 2 — Consolidação`, `Fase 3 — Figuras`, `Fase 4 — Relatório` |
| `labels` | `investigação`, `pergunta-autores`, `figura`, `relatório` — separadas por vírgula |

### Referência a outra issue

Escreva o número do arquivo entre chaves: `{02}`. Na criação, isso vira um
link para a issue correspondente no GitHub, com o número real dela.

---

## Fases

| Fase | Issues | Objetivo |
|---|---|---|
| 1 — Investigação | 01–06 | Explicar por que a Tabela 4 não reproduz |
| 2 — Consolidação | 07–09 | Completar o escopo e fixar a configuração final |
| 3 — Figuras | 10–13 | Figuras e tabelas para o relatório |
| 4 — Relatório | 14–18 | Redação e entrega |

---

## Acrescentar uma issue

1. Crie `roteiro/19-nome-curto.md` no formato acima.
2. Faça commit e push.
3. Rode o workflow de novo — só a nova é criada; as existentes são ignoradas.

**Editar** um arquivo depois que a issue já foi criada não altera a issue no
GitHub. Para isso, edite direto no GitHub.
