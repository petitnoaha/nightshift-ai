#!/usr/bin/env bash
# Objectif : installer Python 3.12+ et créer l'environnement virtuel NightShift
# Officiel : https://www.python.org/downloads/  (Ubuntu utilise son propre dépôt APT)
set -euo pipefail
echo ">> Installation de Python et des outils de base..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

echo ">> Création de l'environnement virtuel dans /opt/nightshift/venv ..."
sudo -u nightshift python3 -m venv /opt/nightshift/venv
sudo -u nightshift /opt/nightshift/venv/bin/pip install --upgrade pip
sudo -u nightshift /opt/nightshift/venv/bin/pip install -r /opt/nightshift/requirements.txt

echo ">> Vérification :"
/opt/nightshift/venv/bin/python3 --version
