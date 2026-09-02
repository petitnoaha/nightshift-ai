"""Agent Coder — implémente une tâche donnée."""
from app.agents.base import Agent


class CoderAgent(Agent):
    name = "coder"

    def system_prompt(self) -> str:
        return (
            "Tu es l'agent Coder de NightShift AI. Tu reçois une tâche précise "
            "et le contexte du projet. Tu dois produire le code complet et "
            "fonctionnel nécessaire (jamais de pseudo-code), en indiquant "
            "clairement le chemin de chaque fichier modifié ou créé."
        )
