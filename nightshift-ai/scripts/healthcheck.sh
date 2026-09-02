#!/usr/bin/env bash
# Objectif : vérifier que tous les services essentiels tournent
set +e
echo "=== NightShift Healthcheck ==="

check() {
  local name="$1"; local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then echo "✓ $name"; else echo "✗ $name"; fi
}

check "PostgreSQL"     "sudo systemctl is-active --quiet postgresql"
check "Ollama"         "curl -sf http://127.0.0.1:11434/api/tags"
check "NightShift API" "curl -sf http://127.0.0.1:8420/api/status"
check "Service nightshift.service" "systemctl is-active --quiet nightshift"

echo "--- Ressources ---"
df -h / | tail -1 | awk '{print "Disque : " $5 " utilisé"}'
free -h | awk '/Mem:/ {print "RAM : " $3 " / " $2}'
