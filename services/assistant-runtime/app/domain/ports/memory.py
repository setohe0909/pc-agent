from typing import Protocol


class MemoryPort(Protocol):
    async def get_context(self, user_id: str) -> dict:
        ...

    async def save_interaction(self, user_id: str, data: dict) -> None:
        ...

    async def save_memory(self, category: str, summary: str) -> bool:
        ...
