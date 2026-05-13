from abc import ABC, abstractmethod
from typing import List, Optional

class CoderWebPort(ABC):
    @abstractmethod
    async def create_repository(self, name: str, stack: str, description: str) -> dict:
        """Crea un repositorio con el stack especificado."""
        pass

    @abstractmethod
    async def adjust_wix_ui(self, site_id: str, changes: str) -> dict:
        """Ajusta la UI de un sitio Wix."""
        pass

    @abstractmethod
    async def get_site_versions(self, site_id: str) -> List[dict]:
        """Obtiene las versiones del sitio."""
        pass

    @abstractmethod
    async def create_site_version(self, site_id: str, label: str) -> dict:
        """Crea una nueva versión/snapshot del sitio."""
        pass
