from backend.agents.base_agent import BaseAgent


class COOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("coo_persona.json")
