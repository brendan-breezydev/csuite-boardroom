from backend.agents.base_agent import BaseAgent


class CTOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("cto_persona.json")
