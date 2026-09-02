"""
Calcule les statistiques affichées sur le dashboard, à partir de :
  - psutil pour CPU / RAM / disque / uptime (données réelles machine)
  - PostgreSQL pour tâches / exécutions / tests / checkpoints

Si une donnée n'est pas disponible (ex : température non lue par le capteur),
on retourne None -> le dashboard affiche "N/A", jamais une valeur inventée.
"""
from __future__ import annotations

import time

import psutil
from sqlalchemy import func, select

from app.database import get_session
from app.models import Checkpoint, Execution, Task, TaskStatus, TestRun

_BOOT_TIME = psutil.boot_time()


def system_stats() -> dict:
    disk = psutil.disk_usage("/")
    temps = None
    try:
        sensors = psutil.sensors_temperatures()
        if sensors:
            first_group = next(iter(sensors.values()))
            if first_group:
                temps = first_group[0].current
    except (AttributeError, NotImplementedError):
        temps = None  # non supporté sur cette machine -> N/A, jamais inventé

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.3),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": disk.percent,
        "uptime_seconds": time.time() - _BOOT_TIME,
        "temperature_celsius": temps,
    }


def project_stats(project_id: str) -> dict:
    with get_session() as session:
        total = session.scalar(select(func.count(Task.id)).where(Task.project_id == project_id)) or 0
        done = session.scalar(
            select(func.count(Task.id)).where(Task.project_id == project_id, Task.status == TaskStatus.DONE)
        ) or 0
        failed = session.scalar(
            select(func.count(Task.id)).where(Task.project_id == project_id, Task.status == TaskStatus.FAILED)
        ) or 0

        exec_total = session.scalar(
            select(func.count(Execution.id)).join(Task).where(Task.project_id == project_id)
        ) or 0
        exec_success = session.scalar(
            select(func.count(Execution.id)).join(Task)
            .where(Task.project_id == project_id, Execution.success.is_(True))
        ) or 0

        tests_passed = session.scalar(select(func.sum(TestRun.passed)).where(TestRun.project_id == project_id)) or 0
        tests_failed = session.scalar(select(func.sum(TestRun.failed)).where(TestRun.project_id == project_id)) or 0

        checkpoints = session.scalar(
            select(func.count(Checkpoint.id)).where(Checkpoint.project_id == project_id)
        ) or 0

    task_success_rate = (done / total * 100) if total else None
    exec_success_rate = (exec_success / exec_total * 100) if exec_total else None
    test_total = tests_passed + tests_failed
    test_success_rate = (tests_passed / test_total * 100) if test_total else None

    return {
        "tasks_total": total,
        "tasks_done": done,
        "tasks_failed": failed,
        "task_success_rate_percent": task_success_rate,
        "executions_total": exec_total,
        "execution_success_rate_percent": exec_success_rate,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "test_success_rate_percent": test_success_rate,
        "checkpoints_count": checkpoints,
    }


def nightshift_score(project_id: str) -> dict:
    """Score /100 basé sur des métriques réelles, avec la formule affichée
    (jamais une boîte noire) :
      40% progression des tâches + 30% réussite des tests
      + 20% stabilité (peu de FAILED) + 10% checkpoints réguliers
    """
    p = project_stats(project_id)
    progress = (p["task_success_rate_percent"] or 0) / 100
    tests = (p["test_success_rate_percent"] or 0) / 100
    stability = 1 - (p["tasks_failed"] / p["tasks_total"]) if p["tasks_total"] else 1
    checkpoint_bonus = min(p["checkpoints_count"] / 10, 1)

    score = 40 * progress + 30 * tests + 20 * stability + 10 * checkpoint_bonus
    return {
        "score": round(score, 1),
        "formula": "40%×progression + 30%×tests + 20%×stabilité + 10%×checkpoints",
        "detail": {
            "progression_percent": p["task_success_rate_percent"],
            "tests_percent": p["test_success_rate_percent"],
            "stability_percent": round(stability * 100, 1),
            "checkpoint_bonus_percent": round(checkpoint_bonus * 100, 1),
        },
    }
