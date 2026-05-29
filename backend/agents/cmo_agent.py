from backend.agents.base_agent import BaseAgent


class CMOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("cmo_persona.json")
