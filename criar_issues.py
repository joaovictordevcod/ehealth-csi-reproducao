#!/usr/bin/env python3
"""
criar_issues.py — Cria no GitHub as issues descritas em roteiro/.

Cada arquivo roteiro/NN-*.md é uma issue. O cabeçalho define título, fase
(milestone) e labels; o restante é o corpo. Ver roteiro/README.md.

Forma recomendada — GitHub Actions:
    Aba Actions → "Criar issues do roteiro" → Run workflow.
    Definido em .github/workflows/criar-issues.yml.

Forma local:
    sudo apt install gh
    gh auth login
    python3 criar_issues.py

Pode ser rodado mais de uma vez: issues e milestones já existentes são
ignorados, identificados pelo título. Para acrescentar uma issue, crie um novo
arquivo em roteiro/ e rode de novo.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).parent / "roteiro"

LABELS = {
    "investigação":     ("1d76db", "Testes e análises para explicar resultados"),
    "pergunta-autores": ("d93f0b", "Questões para o grupo MidiaCom/UFF"),
    "figura":           ("0e8a16", "Figuras e tabelas para o relatório"),
    "relatório":        ("5319e7", "Redação do relatório"),
}

MILESTONES = {
    "Fase 1 — Investigação":  "Explicar por que a Tabela 4 não reproduz.",
    "Fase 2 — Consolidação":  "Completar o escopo e fixar a configuração final.",
    "Fase 3 — Figuras":       "Figuras e tabelas para o relatório.",
    "Fase 4 — Relatório":     "Redação e entrega.",
}


# ─────────────────────────────────────────────────────────────────────────
# Leitura dos arquivos
# ─────────────────────────────────────────────────────────────────────────
def ler_issue(caminho):
    """Lê um arquivo de issue: cabeçalho entre --- e corpo em markdown."""
    texto = caminho.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not m:
        raise ValueError(f"{caminho.name}: cabeçalho --- ausente ou malformado")

    cab = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            cab[k.strip()] = v.strip()

    for campo in ("titulo", "fase", "labels"):
        if campo not in cab:
            raise ValueError(f"{caminho.name}: falta o campo '{campo}'")
    if cab["fase"] not in MILESTONES:
        raise ValueError(f"{caminho.name}: fase desconhecida '{cab['fase']}'")

    labels = [l.strip() for l in cab["labels"].split(",") if l.strip()]
    for l in labels:
        if l not in LABELS:
            raise ValueError(f"{caminho.name}: label desconhecida '{l}'")

    return {
        "numero": caminho.name[:2],
        "titulo": cab["titulo"],
        "fase": cab["fase"],
        "labels": labels,
        "corpo": m.group(2).strip(),
        "arquivo": caminho.name,
    }


def ler_roteiro():
    arquivos = sorted(PASTA.glob("[0-9][0-9]-*.md"))
    if not arquivos:
        sys.exit(f"nenhum arquivo NN-*.md encontrado em {PASTA}")
    issues = [ler_issue(a) for a in arquivos]

    numeros = [i["numero"] for i in issues]
    if len(numeros) != len(set(numeros)):
        sys.exit("há dois arquivos com o mesmo número em roteiro/")
    return issues


# ─────────────────────────────────────────────────────────────────────────
# GitHub
# ─────────────────────────────────────────────────────────────────────────
def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])}: {r.stderr.strip()}")
    return r


def main():
    issues = ler_roteiro()
    print(f"{len(issues)} issues lidas de {PASTA.name}/\n")

    # No GitHub Actions a autenticação vem de GH_TOKEN, definido no workflow.
    em_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    try:
        gh("--version") if em_actions else gh("auth", "status")
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
    for titulo, desc in MILESTONES.items():
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
    # numeração). As issues novas recebem os números seguintes, em ordem,
    # o que permite resolver as referências {NN} antes de criar.
    ult = json.loads(gh("api",
        "repos/{owner}/{repo}/issues?state=all&per_page=1"
        "&sort=created&direction=desc").stdout)
    proximo = (ult[0]["number"] + 1) if ult else 1

    numero = {}
    for i in issues:
        if i["titulo"] in existentes:
            numero[i["numero"]] = existentes[i["titulo"]]
        else:
            numero[i["numero"]] = proximo
            proximo += 1

    def resolve(txt):
        return re.sub(r"\{(\d{2})\}",
                      lambda m: f"#{numero.get(m.group(1), m.group(1))}", txt)

    for i in issues:
        if i["titulo"] in existentes:
            print(f"  já existe: {i['titulo']}")
            continue
        args = ["issue", "create", "--title", i["titulo"],
                "--body", resolve(i["corpo"]), "--milestone", i["fase"]]
        for lb in i["labels"]:
            args += ["--label", lb]
        url = gh(*args).stdout.strip()
        esperado = numero[i["numero"]]
        real = int(url.rstrip("/").split("/")[-1])
        aviso = "" if real == esperado else f"  (!) esperado #{esperado}"
        print(f"  criada: {i['titulo']}  {url}{aviso}")

    print("\nPronto. Veja na aba Issues do repositório.")


if __name__ == "__main__":
    main()
