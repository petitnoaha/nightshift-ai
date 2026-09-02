"""
Gestion des secrets NightShift.

RÈGLE ABSOLUE : un secret n'est JAMAIS écrit dans le code, dans Git,
dans un log, ou affiché à l'écran. Il vit uniquement dans un fichier
sous /opt/nightshift/secrets/, avec permissions 600 (lecture par le
seul utilisateur "nightshift").

Utilisation :
    from app.security.secrets import get_secret
    key = get_secret("anthropic_api_key")   # ou None si absent

Pour définir un secret toi-même sur le ThinkPad (jamais via ce code) :
    sudo -u nightshift bash -c 'echo "sk-xxxx" > /opt/nightshift/secrets/anthropic_api_key.key'
    sudo chmod 600 /opt/nightshift/secrets/anthropic_api_key.key
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

SECRETS_DIR = Path(os.environ.get("NIGHTSHIFT_HOME", "/opt/nightshift")) / "secrets"

KNOWN_SECRETS = (
    "openai_api_key",
    "anthropic_api_key",
    "github_token",
    "cloudflare_token",
    "odoo_password",
    "odoo_api_key",
    "db_password",
)


def get_secret(name: str) -> str | None:
    """Lit un secret depuis secrets/<name>.key. Retourne None si absent.
    Ne loggue jamais la valeur, seulement le fait qu'elle existe ou non."""
    path = SECRETS_DIR / f"{name}.key"
    if not path.exists():
        return None

    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        # Le fichier est lisible par d'autres utilisateurs : on refuse de
        # l'utiliser tant que les permissions ne sont pas corrigées.
        raise PermissionError(
            f"Permissions trop ouvertes sur {path} (attendu 600). "
            f"Corrige avec : chmod 600 {path}"
        )

    value = path.read_text(encoding="utf-8").strip()
    return value or None


def has_secret(name: str) -> bool:
    return get_secret(name) is not None


def redact(text: str, *secret_names: str) -> str:
    """Utilitaire pour s'assurer qu'aucune valeur secrète ne fuite dans un
    message avant de le logguer."""
    out = text
    for name in secret_names:
        value = get_secret(name)
        if value:
            out = out.replace(value, "***REDACTED***")
    return out
