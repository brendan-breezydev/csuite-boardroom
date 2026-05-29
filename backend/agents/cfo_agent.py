from backend.agents.base_agent import BaseAgent


class CFOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("cfo_persona.json")
