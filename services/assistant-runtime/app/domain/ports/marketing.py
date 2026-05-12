from abc import ABC, abstractmethod

class MarketingPort(ABC):
    @abstractmethod
    async def get_comments(self, platform: str, post_id: str) -> list[dict]:
        pass

    @abstractmethod
    async def reply_to_comment(self, platform: str, comment_id: str, text: str) -> bool:
        pass

    @abstractmethod
    async def send_dm(self, platform: str, user_id: str, text: str) -> bool:
        pass

    @abstractmethod
    async def get_competitor_data(self, platform: str, competitor_handle: str) -> dict:
        pass

    @abstractmethod
    async def save_lead(self, lead_data: dict) -> bool:
        pass
