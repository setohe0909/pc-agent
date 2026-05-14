from abc import ABC, abstractmethod
from typing import List, Optional

class CoderWebPort(ABC):
    @abstractmethod
    async def create_repository(self, name: str, stack: str, description: str) -> dict:
        """Crea un repositorio con el stack especificado."""
        pass

