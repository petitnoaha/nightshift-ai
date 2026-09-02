"""Transitions valides de la machine à états NightShift."""
from __future__ import annotations

from app.models import ProjectState

TRANSITIONS: dict[ProjectState, set[ProjectState]] = {
    ProjectState.IDLE: {ProjectState.ANALYZING, ProjectState.STOPPED},
    ProjectState.ANALYZING: {ProjectState.PLANNING, ProjectState.FAILED},
    ProjectState.PLANNING: {ProjectState.EXECUTING, ProjectState.FAILED},
    ProjectState.EXECUTING: {ProjectState.TESTING, ProjectState.WAITING, ProjectState.FAILED, ProjectState.PAUSED},
    ProjectState.TESTING: {ProjectState.REVIEWING, ProjectState.EXECUTING, ProjectState.FAILED},
    ProjectState.REVIEWING: {ProjectState.CHECKPOINT, ProjectState.EXECUTING},
    ProjectState.CHECKPOINT: {ProjectState.NEXT_TASK},
    ProjectState.NEXT_TASK: {ProjectState.ANALYZING, ProjectState.PLANNING, ProjectState.EXECUTING, ProjectState.COMPLETED},
    ProjectState.WAITING: {ProjectState.RECOVERING, ProjectState.PAUSED, ProjectState.STOPPED},
    ProjectState.RECOVERING: {ProjectState.EXECUTING, ProjectState.WAITING, ProjectState.FAILED},
    ProjectState.PAUSED: {ProjectState.EXECUTING, ProjectState.STOPPED},
    ProjectState.FAILED: {ProjectState.RECOVERING, ProjectState.STOPPED},
    ProjectState.STOPPED: {ProjectState.IDLE},
    ProjectState.COMPLETED: {ProjectState.IDLE},
}


class InvalidTransitionError(Exception):
    pass


def transition(current: ProjectState, target: ProjectState) -> ProjectState:
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(f"{current} -> {target} n'est pas autorisé")
    return target
