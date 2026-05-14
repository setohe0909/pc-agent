import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.adapters.open_claw import OpenClawLLMAdapter
from app.use_cases.marketing_graph import MarketingGraph


class FakeLLM:
    async def chat(self, *args, **kwargs):
        return "respuesta generica"

    async def analyze_trade(self, *args, **kwargs):
        return {}

    async def get_tools_response(self, *args, **kwargs):
        raise AssertionError("No deberia consultar al LLM para dashboards explicitos")

    async def generate_image(self, *args, **kwargs):
        return ""


class FakeMemory:
    async def get_context(self, user_id: str):
        return ""

    async def save_interaction(self, user_id: str, data: dict) -> None:
        return None

    async def save_memory(self, category: str, summary: str) -> bool:
        return True


class FakeMarketing:
    def __init__(self):
        self.dashboard_calls = 0

    async def get_comments(self, platform: str, post_id: str):
        return []

    async def reply_to_comment(self, platform: str, comment_id: str, text: str):
        return True

    async def send_dm(self, platform: str, user_id: str, text: str):
        return True

    async def get_competitor_data(self, platform: str, competitor_handle: str):
        return {}

    async def save_lead(self, lead_data: dict):
        return True

    async def get_dashboard(self):
        self.dashboard_calls += 1
        return {
            "status": "success",
            "source": "Zernio Analytics",
            "metrics": {"engagement_rate": "5.8%"},
        }

    async def generate_report(self, report_type: str):
        return {"status": "success", "summary": "ok", "link": "#"}


class MarketingGraphRegressionTests(unittest.TestCase):
    def test_dashboard_prompt_executes_zernio_without_llm_tool_detection(self):
        async def scenario():
            marketing = FakeMarketing()
            graph = MarketingGraph(llm=FakeLLM(), memory=FakeMemory(), marketing=marketing)

            result = await graph.run(
                prompt="Genera un dashboard de mis metricas actuales",
                payload={"sub_command": "chat"},
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("Dashboard Zernio", result["message"])
            self.assertEqual(marketing.dashboard_calls, 1)

        asyncio.run(scenario())

    def test_gemini_tool_schema_uses_uppercase_types(self):
        adapter = OpenClawLLMAdapter()

        tools = [
            {
                "name": "generate_report",
                "description": "Genera un informe",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string"},
                    },
                    "required": ["report_type"],
                },
            }
        ]

        converted = adapter._to_gemini_tools(tools)

        self.assertEqual(converted[0]["parameters"]["type"], "OBJECT")
        self.assertEqual(
            converted[0]["parameters"]["properties"]["report_type"]["type"],
            "STRING",
        )
        self.assertEqual(tools[0]["parameters"]["type"], "object")


if __name__ == "__main__":
    unittest.main()
