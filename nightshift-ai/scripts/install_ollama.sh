#!/usr/bin/env bash
# Objectif : installer Ollama en natif (pas de Docker) pour l'IA locale gratuite
# Officiel : https://ollama.com/download/linux
set -euo pipefail
echo ">> Installation d'Ollama (script officiel)..."
curl -fsSL https://ollama.com/install.sh | sh

echo ">> Téléchargement d'un modèle de départ (adapter selon ta RAM)..."
echo "   RAM limitée (<8 Go) : conseillé 'qwen2.5-coder:1.5b' ou 'qwen2.5-coder:3b'"
echo "   RAM confortable (>=16 Go) : 'qwen2.5-coder:7b'"
ollama pull qwen2.5-coder:7b || echo "Si ça échoue par manque de RAM, relance avec un modèle plus petit."

echo ">> Vérification (ne doit répondre qu'en local, jamais exposé à Internet) :"
curl -s http://127.0.0.1:11434/api/tags
