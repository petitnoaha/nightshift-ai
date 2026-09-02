#!/usr/bin/env bash
# Objectif : créer l'utilisateur Linux dédié "nightshift" et installer le service systemd
set -euo pipefail

if ! id -u nightshift >/dev/null 2>&1; then
  echo ">> Création de l'utilisateur système nightshift (sans shell de connexion)..."
  sudo useradd --system --create-home --home-dir /opt/nightshift --shell /usr/sbin/nologin nightshift
fi

sudo mkdir -p /opt/nightshift
sudo chown -R nightshift:nightshift /opt/nightshift

echo ">> Installation du service systemd..."
sudo cp /opt/nightshift/systemd/nightshift.service /etc/systemd/system/nightshift.service
sudo systemctl daemon-reload
sudo systemctl enable nightshift

echo ">> Le service est activé mais pas encore démarré (démarre-le avec scripts/start.sh une fois la config prête)."
