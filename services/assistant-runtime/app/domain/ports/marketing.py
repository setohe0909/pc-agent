from abc import ABC, abstractmethod

class MarketingPort(ABC):
    @abstractmethod
    async def get_connected_accounts(self) -> dict:
        pass

    @abstractmethod
    async def get_comments(
        self,
        platform: str,
        post_id: str,
        data_source: str | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
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

    @abstractmethod
    async def get_dashboard(self) -> dict:
        pass

    @abstractmethod
    async def generate_report(self, report_type: str) -> dict:
        pass

    @abstractmethod
    async def get_top_content(self, platform: str | None = None, limit: int = 5) -> list[dict]:
        pass

    @abstractmethod
    async def get_audience_insights(self) -> dict:
        pass

    @abstractmethod
    async def get_alerts(self) -> list[dict]:
        pass

    @abstractmethod
    async def get_leads(self, status: str | None = None) -> list[dict]:
        pass

    @abstractmethod
    async def get_whatsapp_outreach(self) -> dict:
        pass

    @abstractmethod
    async def get_best_posting_windows(self) -> dict:
        pass

    @abstractmethod
    async def list_posts(self, platform: str | None = None, limit: int = 10) -> list[dict]:
        pass

    @abstractmethod
    async def save_campaign_draft(self, campaign: dict) -> bool:
        pass

    @abstractmethod
    async def save_post_draft(self, post: dict) -> bool:
        pass

    @abstractmethod
    async def save_automation_run(self, run: dict) -> bool:
        pass

    @abstractmethod
    async def has_processed(self, dedupe_key: str) -> bool:
        pass

    @abstractmethod
    async def schedule_post(self, post: dict) -> bool:
        pass

    @abstractmethod
    async def publish_post(self, post: dict) -> bool:
        pass
