#!/usr/bin/env python3
"""
criar_issues.py — Cria no GitHub as issues com o roteiro do trabalho.

Organiza em quatro fases (milestones) e quatro tipos (labels). As issues são
numeradas no título na ordem em que devem ser feitas.

Forma recomendada — GitHub Actions:
    Aba Actions → "Criar issues do roteiro" → Run workflow.
    Definido em .github/workflows/criar-issues.yml.

Forma local:
    sudo apt install gh
    gh auth login
    python3 criar_issues.py

Pode ser rodado mais de uma vez: issues e milestones já existentes são
ignorados, identificados pelo título.
"""
import json
import os
import re
import subprocess
import sys

LABELS = {
    "investigação":     ("1d76db", "Testes e análises para explicar resultados"),
    "pergunta-autores": ("d93f0b", "Questões para o grupo MidiaCom/UFF"),
    "figura":           ("0e8a16", "Figuras e tabelas para o relatório"),
    "relatório":        ("5319e7", "Redação do relatório"),
}

MILESTONES = [
    ("Fase 1 — Investigação",
     "Explicar por que a Tabela 4 não reproduz."),
    ("Fase 2 — Consolidação",
     "Completar o escopo e fixar a configuração final."),
    ("Fase 3 — Figuras",
     "Figuras e tabelas para o relatório."),
    ("Fase 4 — Relatório",
     "Redação e entrega."),
]

F1, F2, F3, F4 = (m[0] for m in MILESTONES)

ISSUES = [
    # ─────────────────────────── FASE 1 ───────────────────────────
    ("01 · Enviar perguntas ao grupo MidiaCom", F1, ["pergunta-autores"], """
## Contexto

Várias divergências entre o dado descrito nos artigos e o dataset publicado
só podem ser resolvidas por quem fez a coleta. As respostas mudam a
interpretação dos resultados — vale enviar cedo, em paralelo às investigações.

## Perguntas

1. **O DS1 está disponível?** Os artigos descrevem o protocolo DS1 (~8 Hz); o
   dataset recebido é DS2 (~33 Hz).
2. **De onde vêm os 18 participantes da Tabela 4?** O artigo menciona 118
   participantes; o `valid.txt` do DS2 lista 106, dos quais 100 completos. A
   conta não fecha.
3. **A coleta contínua de 6 horas de sala vazia citada no LATINCOM está
   disponível? Foi usada no IEEE Access?**
4. **Como foram obtidas as 1700 instâncias de sala vazia?** Existe uma única
   gravação de posição 0 por participante no DS2.

## Concluído quando

- [ ] Mensagem enviada
- [ ] Resposta registrada no `DIARIO.md`
- [ ] Decisões afetadas atualizadas no `DECISOES.md`
"""),

    ("02 · Medir deriva do ambiente ao longo da coleta", F1, ["investigação"], """
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
"""),

    ("03 · Usar referência de sala vazia contemporânea", F1, ["investigação"], """
## Depende de

{02} — só faz sentido se a deriva for confirmada.

## Contexto

Hoje todas as features são distâncias DTW contra **uma** referência, a sala
vazia do participante 001. Se o ambiente derivou, essa referência é inadequada
para participantes coletados meses depois.

O uso real do método é calibrar o sistema com a sala vazia **no momento** e
então detectar presença. Uma referência contemporânea é mais fiel a isso — e
provavelmente é o que os autores tinham implicitamente, já que o LATINCOM
trabalhou com 25 participantes num período curto.

## O que fazer

- Para cada participante, usar como referência a sala vazia de um
  participante **vizinho no tempo** (por exemplo, o anterior), nunca a do
  próprio participante — senão a classe 0 vira distância de si mesmo.
- Rodar apenas o protocolo por participante (holdout), com segmentos de 29
  amostras, sem sobreposição.
- Comparar com o resultado da referência única.

## Concluído quando

- [ ] Opção implementada em `build_dataset`, sem remover a referência única
- [ ] Comparação registrada no `DIARIO.md`
- [ ] Decisão registrada no `DECISOES.md`
"""),

    ("04 · Sensibilidade ao pré-processamento (Hampel e média móvel)", F1,
     ["investigação"], """
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
"""),

    ("05 · Sensibilidade ao fator de subamostragem", F1, ["investigação"], """
## Contexto

O pipeline subamostra o DS2 por 4 (de ~33 Hz para ~8,7 Hz) para aproximar a
taxa do DS1 descrita nos artigos e reduzir o custo do DTW. Isso descarta 3/4
das amostras.

## O que fazer

Testar fatores 1, 2, 4 e 8, mantendo a **duração** do segmento constante
(~3,3 s) — ou seja, ajustando `seg_len` em amostras para cada fator.

Atenção ao custo: fator 1 multiplica o tempo do DTW por ~16. Medir numa
amostra de participantes antes de rodar tudo.

## Concluído quando

- [ ] Resultados em `.csv`, versionados
- [ ] Registro no `DIARIO.md`
"""),

    ("06 · Variante de DTW e normalização das séries", F1, ["investigação"], """
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
"""),

    # ─────────────────────────── FASE 2 ───────────────────────────
    ("07 · Rodar o cenário desbalanceado", F2, ["investigação"], """
## Contexto

O escopo inclui dados balanceados **e** desbalanceados. O desbalanceado ainda
não foi executado.

No LATINCOM, o NB registra 79,41% de acurácia no desbalanceado, mas 46,55% de
precisão e 44,26% de F-measure — a acurácia esconde que o modelo classifica
quase tudo como a classe majoritária.

## O que fazer

- Usar **gravações completas** (500 amostras) nas duas classes, sem
  fragmentar: 1700 ocupadas contra ~100 vazias. Isso elimina a sobreposição e
  usa todo o sinal disponível.
- Reportar acurácia, precisão, recall e F1 — não só acurácia.
- Avaliar nos dois protocolos.

## Concluído quando

- [ ] Resultado registrado no `DIARIO.md`
- [ ] Comparação qualitativa com o padrão relatado no LATINCOM
"""),

    ("08 · Seleção de atributos sem vazamento", F2, ["investigação"], """
## Contexto

O LATINCOM relata que 5 atributos selecionados atingem 99,98% com RF, e que
acima de 20 a acurácia declina. A seleção rodada até agora usou a divisão
aleatória, que está sujeita a vazamento quando há sobreposição.

## O que fazer

- Rodar `SelectKBest` com k em 5, 10, 20, 50, 100, 234.
- Features de 29 amostras, sem sobreposição.
- Protocolo por participante, com a seleção ajustada **apenas no treino**.

## Concluído quando

- [ ] Curva registrada no `DIARIO.md`
- [ ] Comparação com a Figura 3 do LATINCOM
"""),

    ("09 · Fixar a configuração final e fazer a execução de referência", F2,
     ["investigação"], """
## Depende de

{02} a {08}.

## O que fazer

- Com base nas investigações, escolher a configuração final de todos os
  parâmetros em `PARAMS`.
- Executar uma última vez, do zero.
- Gerar o `registro_execucao.json` definitivo.
- Marcar o commit com uma tag: `git tag execucao-final`.

## Concluído quando

- [ ] `DECISOES.md` reflete exatamente a configuração final
- [ ] Execução registrada no `DIARIO.md`
- [ ] Tag criada e enviada
"""),

    # ─────────────────────────── FASE 3 ───────────────────────────
    ("10 · Figura: duração do segmento nos dois protocolos", F3, ["figura"], """
## Conteúdo

Acurácia × duração do segmento, com duas séries: divisão aleatória e
participantes não vistos. Eixo secundário ou anotação com a sobreposição das
janelas.

É a figura central do achado de vazamento: a divisão aleatória sobe com a
sobreposição, o teste por participante não.

## Fonte

`varredura_duracao.csv`

## Concluído quando

- [ ] Script que gera a figura, versionado
- [ ] Figura em `docs/figuras/`
"""),

    ("11 · Figura: sensibilidade à escolha dos participantes de teste", F3,
     ["figura"], """
## Conteúdo

Distribuição das acurácias nos 20 sorteios, com marcas para "primeiros 18",
"últimos 18" e o valor publicado.

## Fonte

`teste_holdout.csv` — ajustar o script para salvar também os 20 valores
individuais, não só o resumo.

## Concluído quando

- [ ] Script que gera a figura, versionado
- [ ] Figura em `docs/figuras/`
"""),

    ("12 · Figura: deriva do ambiente", F3, ["figura"], """
## Depende de

{02} — só se a deriva for confirmada.

## Conteúdo

Distância média até a referência × identificador do participante, uma série
por classe.

## Concluído quando

- [ ] Script que gera a figura, versionado
- [ ] Figura em `docs/figuras/`
"""),

    ("13 · Tabela consolidada: obtido × publicado", F3, ["figura"], """
## Depende de

{09}.

## Conteúdo

Uma tabela com, para cada classificador e cada protocolo: valor publicado,
valor obtido na configuração final e diferença. Incluir nota indicando qual
configuração foi usada e remetendo ao `DECISOES.md`.

## Concluído quando

- [ ] Tabela em `docs/`
"""),

    # ─────────────────────────── FASE 4 ───────────────────────────
    ("14 · Relatório: estrutura e introdução", F4, ["relatório"], """
## Conteúdo

- Definir a estrutura e o formato exigido pela disciplina.
- Introdução: sensoriamento Wi-Fi por CSI, detecção de presença, o problema da
  reprodutibilidade na área, objetivo do trabalho.
- Deixar explícito que o trabalho é reprodução, não método novo.

## Fontes

`README.md`, seção "Objetivo"; os dois artigos de referência.
"""),

    ("15 · Relatório: método", F4, ["relatório"], """
## Conteúdo

- Dataset: DS2, estrutura, integridade, diferença em relação ao DS1.
- Pipeline: leitura, máscara de subportadoras, pré-processamento, DTW,
  construção das classes, classificadores.
- Protocolos de avaliação: divisão aleatória e participantes não vistos.
- **Todas** as decisões não documentadas nos artigos, com justificativa.

## Fonte

`DECISOES.md` — esta seção é, em grande parte, a transcrição dele em prosa.
"""),

    ("16 · Relatório: resultados", F4, ["relatório"], """
## Conteúdo

- Tabela consolidada ({13}).
- O artefato de comprimento entre classes e sua correção.
- O efeito da sobreposição: figura {10}.
- Sensibilidade à escolha dos participantes: figura {11}.
- Deriva, se confirmada: figura {12}.
- Seleção de atributos e cenário desbalanceado.

## Fonte

`DIARIO.md`, entradas de 2026-09-23 em diante.
"""),

    ("17 · Relatório: discussão, limitações e ameaças à validade", F4,
     ["relatório"], """
## Conteúdo

- O que reproduziu e o que não reproduziu.
- Quais decisões não documentadas mais afetaram o resultado.
- Diferenças entre o dado descrito e o dado publicado: DS1 × DS2, as 1700
  instâncias de sala vazia, os 18 participantes de teste.
- Limitações: substituição do J48, composição do holdout, fragmentação das
  gravações de sala vazia.
- O que faltaria nos artigos originais para uma reprodução completa.
- Respostas do grupo MidiaCom, se houver ({01}).

Tom: registrar divergências como achados, não como crítica aos autores.
"""),

    ("18 · Revisão final e entrega", F4, ["relatório"], """
## Checklist

- [ ] Todo número citado no relatório bate com um arquivo de resultados
- [ ] Toda decisão citada está no `DECISOES.md`
- [ ] Figuras reproduzíveis pelos scripts versionados
- [ ] README atualizado com o estado final
- [ ] Referências completas
- [ ] Revisão de texto
- [ ] Entrega
"""),
]


def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])}: {r.stderr.strip()}")
    return r


def main():
    # No GitHub Actions a autenticação vem de GH_TOKEN, definido no workflow.
    em_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    try:
        if not em_actions:
            gh("auth", "status")
        else:
            gh("--version")
    except FileNotFoundError:
        sys.exit("gh não instalado. Rode: sudo apt install gh")
    except RuntimeError:
        sys.exit("gh não autenticado. Rode: gh auth login")

    print("Labels")
    for nome, (cor, desc) in LABELS.items():
        r = gh("label", "create", nome, "--color", cor,
               "--description", desc, check=False)
        print(f"  {'criada' if r.returncode == 0 else 'já existe'}: {nome}")

    print("\nMilestones")
    existentes = {m["title"] for m in json.loads(
        gh("api", "repos/{owner}/{repo}/milestones?state=all&per_page=100").stdout)}
    for titulo, desc in MILESTONES:
        if titulo in existentes:
            print(f"  já existe: {titulo}")
            continue
        gh("api", "repos/{owner}/{repo}/milestones",
           "-f", f"title={titulo}", "-f", f"description={desc}")
        print(f"  criado: {titulo}")

    print("\nIssues")
    existentes = {i["title"]: i["number"] for i in json.loads(
        gh("issue", "list", "--state", "all", "--limit", "300",
           "--json", "title,number").stdout)}

    # Maior número já usado no repositório (issues e PRs compartilham a
    # numeração). As issues novas recebem os números seguintes, em ordem.
    ult = json.loads(gh("api",
        "repos/{owner}/{repo}/issues?state=all&per_page=1"
        "&sort=created&direction=desc").stdout)
    proximo = (ult[0]["number"] + 1) if ult else 1

    numero = {}
    for titulo, *_ in ISSUES:
        nn = titulo[:2]
        if titulo in existentes:
            numero[nn] = existentes[titulo]
        else:
            numero[nn] = proximo
            proximo += 1

    def resolve(txt):
        return re.sub(r"\{(\d{2})\}",
                      lambda m: f"#{numero.get(m.group(1), m.group(1))}", txt)

    for titulo, milestone, labels, corpo in ISSUES:
        if titulo in existentes:
            print(f"  já existe: {titulo}")
            continue
        args = ["issue", "create", "--title", titulo,
                "--body", resolve(corpo.strip()), "--milestone", milestone]
        for lb in labels:
            args += ["--label", lb]
        url = gh(*args).stdout.strip()
        esperado = numero[titulo[:2]]
        real = int(url.rstrip("/").split("/")[-1])
        aviso = "" if real == esperado else f"  (!) esperado #{esperado}"
        print(f"  criada: {titulo}  {url}{aviso}")

    print("\nPronto. Veja em: gh issue list  ou  na aba Issues do repositório.")


if __name__ == "__main__":
    main()
