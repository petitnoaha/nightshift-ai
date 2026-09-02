#!/usr/bin/env bash
# Objectif : accès distant sécurisé au dashboard SANS ouvrir de port sur la box.
# Comme tu n'as pas encore de nom de domaine, on utilise un "quick tunnel"
# gratuit (URL temporaire en *.trycloudflare.com). Le jour où tu as un domaine,
# on passera à un tunnel nommé (voir README, section Cloudflare).
# Officiel : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
set -euo pipefail
echo ">> Téléchargement de cloudflared..."
curl -L --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb

echo ">> Test rapide (Ctrl+C pour arrêter) :"
echo "   cloudflared tunnel --url http://127.0.0.1:8420"
echo "   Une URL du type https://xxxx.trycloudflare.com s'affichera : c'est ton dashboard à distance."
