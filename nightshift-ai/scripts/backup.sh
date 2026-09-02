#!/usr/bin/env bash
# Objectif : sauvegarder la base PostgreSQL + l'état + la config
# À planifier avec cron : 0 6 * * * /opt/nightshift/scripts/backup.sh
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
DEST="/opt/nightshift/backups/${STAMP}"
mkdir -p "${DEST}"

sudo -u postgres pg_dump nightshift_db > "${DEST}/nightshift_db.sql"
cp -r /opt/nightshift/data "${DEST}/data" 2>/dev/null || true
cp -r /opt/nightshift/config "${DEST}/config" 2>/dev/null || true

# Rotation : ne garder que les 14 dernières sauvegardes
cd /opt/nightshift/backups
ls -1t | tail -n +15 | xargs -r rm -rf

echo "Sauvegarde créée : ${DEST}"
