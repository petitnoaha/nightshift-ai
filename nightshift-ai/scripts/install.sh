#!/usr/bin/env bash
# Installation complète, dans l'ordre. Relançable sans risque (idempotent).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "############################################"
echo "# Installation de NightShift AI (sans Docker)"
echo "############################################"

bash "${SCRIPT_DIR}/configure_systemd.sh"
bash "${SCRIPT_DIR}/install_python.sh"
bash "${SCRIPT_DIR}/install_postgresql.sh"
bash "${SCRIPT_DIR}/install_ollama.sh"
bash "${SCRIPT_DIR}/install_cloudflare.sh"
bash "${SCRIPT_DIR}/healthcheck.sh"

echo "############################################"
echo "# Installation terminée."
echo "# Démarre NightShift avec : bash scripts/start.sh"
echo "############################################"
