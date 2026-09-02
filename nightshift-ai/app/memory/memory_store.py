"""
Mémoire de travail — sauvegarde l'état exact d'une tâche en cours sur disque,
en plus de la base PostgreSQL, pour pouvoir reprendre après :
  - un redémarrage du ThinkPad
  - un crash du processus NightShift
  - une coupure de courant

L'état est un simple JSON par projet : /opt/nightshift/data/state_<project_id>.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("NIGHTSHIFT_HOME", "/opt/nightshift")) / "data"


def _path(project_id: str) -> Path:
    return DATA_DIR / f"state_{project_id}.json"


def save_state(project_id: str, state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = _path(project_id).with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    tmp_path.replace(_path(project_id))  # écriture atomique : jamais de fichier à moitié écrit


def load_state(project_id: str) -> dict[str, Any] | None:
    path = _path(project_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_state(project_id: str) -> None:
    path = _path(project_id)
    if path.exists():
        path.unlink()
