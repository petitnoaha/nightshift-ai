"""Agent Planner — découpe l'objectif du projet en tâches concrètes."""
from app.agents.base import Agent


class PlannerAgent(Agent):
    name = "planner"

    def system_prompt(self) -> str:
        return (
            "Tu es le Planner de NightShift AI. Ton rôle est d'analyser l'état "
            "actuel d'un projet logiciel et de produire une liste de tâches "
            "concrètes, ordonnées, réalisables une par une par un agent Coder. "
            "Chaque tâche doit être petite, testable, et clairement décrite. "
            "Réponds sous forme de liste numérotée, sans blabla inutile."
        )
