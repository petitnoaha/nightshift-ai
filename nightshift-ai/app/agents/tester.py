"""Agent Tester — écrit et/ou exécute les tests, rapporte les résultats."""
from app.agents.base import Agent


class TesterAgent(Agent):
    name = "tester"

    def system_prompt(self) -> str:
        return (
            "Tu es l'agent Tester de NightShift AI. À partir du code fourni, "
            "tu écris des tests pertinents (ou indiques comment exécuter les "
            "tests existants) et rapportes précisément : nombre de tests "
            "passés, échoués, ignorés, et la cause de chaque échec."
        )
