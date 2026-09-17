#!/usr/bin/env bash
# Inicializa o repositório git e envia para o GitHub.
# Antes de rodar: crie o repositório vazio em https://github.com/new
# com o nome ehealth-csi-reproducao, SEM marcar "Add a README".
set -e

git init
git add .
git commit -m "Reprodução do experimento de detecção de presença por Wi-Fi CSI

Pipeline completo (leitura dos .npz, pré-processamento, DTW, classificação),
documentação das decisões de reprodução e diário de pesquisa.

Estado: pendente a execução final com a correção do DTW."
git branch -M main
git remote add origin https://github.com/joaovictordevcod/ehealth-csi-reproducao.git
git push -u origin main
