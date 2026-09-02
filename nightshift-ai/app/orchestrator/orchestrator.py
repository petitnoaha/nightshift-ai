"""
Orchestrateur NightShift — fait avancer un projet à travers la machine à états,
en s'appuyant sur les 4 agents, en checkpointant avec Git, et en gérant les
coupures de provider via le RetryScheduler, sans jamais perdre l'état.
"""
from __future__ import annotations

import logging
import time

from app.agents.coder import CoderAgent
from app.agents.planner import PlannerAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.tester import TesterAgent
from app.config import ProjectConfig, settings
from app.database import get_session
from app.git.git_manager import GitManager
from app.memory.memory_store import clear_state, load_state, save_state
from app.models import Project, ProjectState, Task, TaskStatus
from app.orchestrator.state_machine import transition
from app.providers.base import ProviderUnavailableError
from app.providers.manager import ProviderManager
from app.scheduler.retry import RetryScheduler

logger = logging.getLogger("nightshift.orchestrator")


class ProjectOrchestrator:
    def __init__(self, project_cfg: ProjectConfig) -> None:
        self.cfg = project_cfg
        self.provider_manager = ProviderManager()
        self.scheduler = RetryScheduler(self.provider_manager)
        self.git = GitManager(project_cfg.workspace, settings.git.branch_prefix if hasattr(settings, "git") else "nightshift")

        self.agents = {
            "planner": PlannerAgent(self.provider_manager),
            "coder": CoderAgent(self.provider_manager),
            "tester": TesterAgent(self.provider_manager),
            "reviewer": ReviewerAgent(self.provider_manager),
        }
        self.state = ProjectState.IDLE

    def _ensure_project_row(self) -> Project:
        with get_session() as session:
            project = session.get(Project, self.cfg.id)
            if project is None:
                project = Project(id=self.cfg.id, name=self.cfg.name, workspace=self.cfg.workspace)
                session.add(project)
            return project

    async def run_forever(self) -> None:
        """Boucle principale — reprend l'état existant si le processus a redémarré."""
        saved = load_state(self.cfg.id)
        if saved:
            logger.info("Reprise d'un état sauvegardé pour %s : %s", self.cfg.id, saved.get("current_task"))
            self.state = ProjectState(saved.get("state", ProjectState.IDLE.value))
        else:
            self.state = ProjectState.IDLE

        self._ensure_project_row()

        while self.state not in (ProjectState.STOPPED, ProjectState.COMPLETED):
            try:
                await self._step()
            except ProviderUnavailableError:
                self._save_current_state()
                self.state = transition(self.state, ProjectState.WAITING)
                await self.scheduler.wait_for_provider(on_alert=self._alert_provider_down)
                self.state = transition(self.state, ProjectState.RECOVERING)
            except Exception:
                logger.exception("Erreur inattendue dans l'orchestrateur, passage en FAILED")
                self._save_current_state()
                self.state = transition(self.state, ProjectState.FAILED)

    async def _step(self) -> None:
        """Un pas de la machine à états. Version volontairement simple pour V1 :
        Planner -> Coder -> Tester -> Reviewer -> Checkpoint -> tâche suivante."""
        if self.state == ProjectState.IDLE:
            self.state = transition(self.state, ProjectState.ANALYZING)

        elif self.state == ProjectState.ANALYZING:
            self.state = transition(self.state, ProjectState.PLANNING)

        elif self.state == ProjectState.PLANNING:
            result = await self.agents["planner"].run(
                f"Planifie la prochaine tâche pour le projet {self.cfg.name}", {}
            )
            self._create_task_from_plan(result.output)
            self.state = transition(self.state, ProjectState.EXECUTING)

        elif self.state == ProjectState.EXECUTING:
            await self.agents["coder"].run(self._current_task_title(), {"project": self.cfg.name})
            self.state = transition(self.state, ProjectState.TESTING)

        elif self.state == ProjectState.TESTING:
            await self.agents["tester"].run(self._current_task_title(), {"project": self.cfg.name})
            self.state = transition(self.state, ProjectState.REVIEWING)

        elif self.state == ProjectState.REVIEWING:
            await self.agents["reviewer"].run(self._current_task_title(), {"project": self.cfg.name})
            self.state = transition(self.state, ProjectState.CHECKPOINT)

        elif self.state == ProjectState.CHECKPOINT:
            self.git.checkpoint(task_id=1, label="auto-checkpoint")
            clear_state(self.cfg.id)
            self.state = transition(self.state, ProjectState.NEXT_TASK)

        elif self.state == ProjectState.NEXT_TASK:
            self.state = transition(self.state, ProjectState.PLANNING)

        elif self.state == ProjectState.RECOVERING:
            self.state = transition(self.state, ProjectState.EXECUTING)

    def _current_task_title(self) -> str:
        return getattr(self, "_last_task_title", "Tâche en cours")

    def _create_task_from_plan(self, plan_text: str) -> None:
        first_line = next((l for l in plan_text.splitlines() if l.strip()), "Tâche")
        self._last_task_title = first_line
        with get_session() as session:
            task = Task(project_id=self.cfg.id, title=first_line, status=TaskStatus.IN_PROGRESS)
            session.add(task)

    def _save_current_state(self) -> None:
        save_state(self.cfg.id, {
            "state": self.state.value,
            "current_task": self._current_task_title(),
            "saved_at": time.time(),
        })

    def _alert_provider_down(self, attempts: int) -> None:
        logger.error(
            "ALERTE : aucun provider IA disponible après %s tentatives pour le projet %s",
            attempts, self.cfg.name,
        )
