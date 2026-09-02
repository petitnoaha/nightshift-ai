#!/usr/bin/env bash
# Objectif : installer PostgreSQL et créer la base + l'utilisateur NightShift
# Officiel : https://www.postgresql.org/download/linux/ubuntu/
set -euo pipefail
echo ">> Installation de PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

echo ">> Création de la base et de l'utilisateur (mot de passe demandé une seule fois)..."
read -rsp "Choisis un mot de passe pour l'utilisateur PostgreSQL nightshift_user : " DB_PASSWORD
echo
sudo -u postgres psql -c "CREATE USER nightshift_user WITH PASSWORD '${DB_PASSWORD}';" || true
sudo -u postgres psql -c "CREATE DATABASE nightshift_db OWNER nightshift_user;" || true

echo ">> Enregistrement du mot de passe dans secrets/ (jamais dans le code)..."
sudo mkdir -p /opt/nightshift/secrets
echo -n "${DB_PASSWORD}" | sudo tee /opt/nightshift/secrets/db_password.key > /dev/null
sudo chown nightshift:nightshift /opt/nightshift/secrets/db_password.key
sudo chmod 600 /opt/nightshift/secrets/db_password.key
unset DB_PASSWORD

echo ">> Vérification :"
sudo -u postgres psql -c "\l" | grep nightshift_db
