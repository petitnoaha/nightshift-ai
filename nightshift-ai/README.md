# 🌙 NightShift AI

Orchestrateur autonome d'agents IA (Planner → Coder → Tester → Reviewer) qui
fait avancer tes projets pendant la nuit, sans Docker, entièrement natif sur
Ubuntu avec systemd. Serveur cible : ton **ThinkPad**, qui doit rester allumé
24h/24. Ton PC gaming n'a besoin d'être allumé pour rien.

⚠️ **État de ce livrable** : c'est une base V1 fonctionnelle et honnête —
config, base de données, sécurité, agents, orchestrateur, scheduler de
relance, statistiques réelles, dashboard, scripts d'install, service systemd.
Ce qui reste volontairement simplifié pour une V1 tenable : la synchronisation
Odoo (V2, désactivée par défaut) et le tunnel Cloudflare nommé (tu n'as pas
encore de domaine — on utilise un tunnel gratuit temporaire en attendant).
Dis-moi une fois que tu as testé cette base et on enchaîne sur la suite.

---

## 1. Comptes à créer avant de commencer

| Compte | Obligatoire | Pourquoi |
|---|---|---|
| Utilisateur Linux `nightshift` | Oui | créé automatiquement par `scripts/configure_systemd.sh`, pas de compte web à créer |
| GitHub | Oui | checkpoints et versioning de tes projets — https://github.com/signup |
| Cloudflare | Recommandé | accès au dashboard à distance sans ouvrir de port — https://dash.cloudflare.com/sign-up |
| Odoo | Optionnel (V2) | interface de gestion — pas nécessaire pour démarrer |
| Ollama | Aucun compte requis | tourne 100% en local |

Tu n'as **jamais** à me donner une clé API, un mot de passe ou un token. Tu les
configures toi-même directement sur le ThinkPad (étape 6).

---

## 2. Liens officiels d'installation

| Logiciel | Lien officiel | Pourquoi | Version conseillée |
|---|---|---|---|
| Ubuntu Desktop | https://ubuntu.com/download/desktop | système du ThinkPad | 24.04 LTS |
| Python | https://www.python.org/downloads/ (via APT sur Ubuntu) | exécute NightShift | 3.12+ |
| Git | https://git-scm.com/downloads | versioning et checkpoints | dernière stable |
| PostgreSQL | https://www.postgresql.org/download/linux/ubuntu/ | base de données | 16 |
| Ollama | https://ollama.com/download/linux | IA locale gratuite | dernière stable |
| Odoo Community | https://www.odoo.com/documentation/17.0/administration/on_premise/source.html | interface de gestion (V2) | 17.0 |
| Nginx | https://nginx.org/en/download.html | reverse proxy local (optionnel si tu passes par Cloudflare directement) | dernière stable |
| Cloudflare Tunnel (cloudflared) | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ | accès distant sécurisé sans ouvrir de port | dernière stable |
| Node.js (optionnel) | https://nodejs.org/en/download | seulement si un de tes projets en a besoin | LTS |

---

## 3. Procédure complète, du ThinkPad vierge au dashboard

### Étape 1 — Préparer la clé USB Ubuntu
1. Télécharge l'image ISO : https://ubuntu.com/download/desktop
2. Crée la clé USB avec Rufus (Windows) ou Balena Etcher (multi-plateforme) : https://etcher.balena.io/
3. Démarre le ThinkPad sur la clé USB et installe Ubuntu Desktop 24.04.

### Étape 2 — Mise à jour du système
```bash
sudo apt update && sudo apt full-upgrade -y
```
**Résultat attendu** : aucune erreur, éventuellement un redémarrage demandé.

### Étape 3 — Économiser les ressources (ThinkPad ancien + Desktop)
Comme tu as choisi Ubuntu Desktop (interface graphique) plutôt que Server, tu
peux éviter que l'interface graphique se lance à chaque démarrage — ça libère
de la RAM et du CPU pour NightShift, sans avoir à réinstaller quoi que ce soit :
```bash
sudo systemctl set-default multi-user.target   # démarre sans interface graphique
# Pour revenir à l'interface graphique un jour : sudo systemctl set-default graphical.target
```
Tu pourras toujours te connecter au ThinkPad à distance en SSH ou via le dashboard web.

### Étape 4 — Récupérer le projet
```bash
sudo mkdir -p /opt/nightshift
sudo chown $USER:$USER /opt/nightshift
git clone <URL_DE_TON_DEPOT_GITHUB> /opt/nightshift
cd /opt/nightshift
```
(Si tu n'as pas encore mis ce projet sur GitHub, copie simplement les fichiers dans `/opt/nightshift`.)

### Étape 5 — Installation automatique
```bash
cd /opt/nightshift
bash scripts/install.sh
```
Ce script, dans l'ordre : crée l'utilisateur `nightshift`, installe Python +
l'environnement virtuel, PostgreSQL (te demande un mot de passe une seule
fois, jamais réaffiché), Ollama + un premier modèle, cloudflared, puis lance
un healthcheck. **Résultat attendu** : que des `✓` à la fin.

### Étape 6 — Configurer les secrets (toi-même, jamais l'IA)
```bash
sudo -u nightshift bash -c 'echo "TA_CLE" > /opt/nightshift/secrets/anthropic_api_key.key'
sudo chmod 600 /opt/nightshift/secrets/anthropic_api_key.key
```
Répète pour `openai_api_key`, `github_token`, `cloudflare_token`, `odoo_password`, `odoo_api_key` — uniquement ceux dont tu as besoin. Le mot de passe PostgreSQL a déjà été enregistré automatiquement à l'étape 5.

### Étape 7 — Adapter la configuration
Ouvre `config/config.yaml`, vérifie/complète au minimum :
- `providers.ollama.model` (le modèle que tu as téléchargé)
- `projects[0].git_remote` (l'URL de ton dépôt GitHub pour Project Island)

### Étape 8 — Démarrer NightShift
```bash
bash scripts/start.sh
```
**Résultat attendu** : `Active: active (running)`.

### Étape 9 — Vérifier
```bash
bash scripts/healthcheck.sh
```

### Étape 10 — Accéder au dashboard
En local sur le ThinkPad : http://127.0.0.1:8420
À distance (tunnel temporaire, pas encore de domaine) :
```bash
cloudflared tunnel --url http://127.0.0.1:8420
```
Une URL `https://xxxx.trycloudflare.com` s'affiche — ouvre-la depuis n'importe quel appareil. Elle change à chaque relance du tunnel ; le jour où tu achètes un domaine, dis-le-moi et on passera à un tunnel nommé permanent.

---

## 4. Vie quotidienne

| Action | Commande |
|---|---|
| Démarrer | `bash scripts/start.sh` |
| Arrêter | `bash scripts/stop.sh` |
| Voir les logs en direct | `journalctl -u nightshift -f` |
| Vérifier la santé | `bash scripts/healthcheck.sh` |
| Sauvegarder maintenant | `bash scripts/backup.sh` |
| Sauvegarde automatique quotidienne | `crontab -e` puis ajouter `0 6 * * * /opt/nightshift/scripts/backup.sh` |

---

## 5. Sécurité — ce qui est déjà en place

- Utilisateur Linux dédié `nightshift`, sans droits root, sans shell de connexion.
- `systemd` sandboxing (`ProtectSystem=strict`, `ProtectHome=true`, accès disque limité aux dossiers du projet).
- Allowlist de commandes (`app/security/command_policy.py`) : un agent ne peut exécuter que `git`, `python`, `pytest`, `npm`, `node`, `cargo`, `make` — tout le reste est bloqué ou demande une validation humaine.
- Secrets uniquement dans `/opt/nightshift/secrets/*.key`, permissions 600, jamais dans le code/Git/logs.
- Ollama jamais exposé à Internet (127.0.0.1 uniquement).
- Accès distant uniquement via Cloudflare Tunnel — aucun port ouvert sur ta box.

À faire toi-même en plus si tu veux aller plus loin : activer UFW (`sudo ufw enable`, tout bloquer sauf loopback puisque Cloudflare gère l'accès distant) et envisager AppArmor pour le processus Python.

---

## 6. Reprise après redémarrage ou crash

NightShift sauvegarde l'état de la tâche en cours dans
`/opt/nightshift/data/state_<projet>.json` avant chaque risque de coupure. Au
redémarrage du service (boot ou crash), il recharge cet état et reprend
exactement où il s'était arrêté — jamais de tâche relancée depuis zéro. Quand
un provider IA est indisponible, le projet passe en `WAITING`, une nouvelle
tentative a lieu toutes les 60 minutes (`scheduler.retry_interval_minutes`
dans `config.yaml`) jusqu'à ce qu'il redevienne joignable.

---

## 7. Dépannage rapide

- **Le service ne démarre pas** : `journalctl -u nightshift -e` pour voir l'erreur exacte.
- **Ollama ne répond pas** : `sudo systemctl status ollama` ; sinon relance avec `ollama serve`.
- **PostgreSQL refuse la connexion** : vérifie que `secrets/db_password.key` correspond bien au mot de passe créé à l'étape 5.
- **Le dashboard n'affiche rien** : vérifie `curl http://127.0.0.1:8420/api/status`.

---

## 8. Structure du projet

```
/opt/nightshift/
├── app/            # code (api, orchestrator, agents, providers, security, statistics...)
├── dashboard/       # interface web
├── config/          # config.yaml (versionné) + config.local.yaml (perso, non versionné)
├── scripts/         # installation, start/stop, backup, healthcheck
├── systemd/         # service nightshift.service
├── secrets/         # clés — jamais versionné
├── data/            # état de reprise — jamais versionné
├── logs/            # jamais versionné
└── backups/         # jamais versionné
```
