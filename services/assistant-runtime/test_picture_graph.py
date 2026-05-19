import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.domain.picture.models import PictureEditPlan, PictureOperation
from app.adapters.open_claw import OpenClawLLMAdapter
from app.main import _decode_request_images
from app.use_cases.picture_graph import PictureGraph


class FakePictureLLM:
    def __init__(self, analysis: str | None = None):
        self.analysis = analysis
        self.chat_calls = []
        self.generate_calls = []
        self.edit_calls = []

    async def chat(self, prompt: str, context=None, images=None, system_instruction=None) -> str:
        self.chat_calls.append(
            {
                "prompt": prompt,
                "images": images,
                "system_instruction": system_instruction,
            }
        )
        if "Verifica el resultado" in prompt:
            return json.dumps(
                {
                    "passed": True,
                    "confidence": 0.92,
                    "findings": ["Replacement text is present", "Layout appears preserved"],
                    "requires_human_review": False,
                }
            )
        if self.analysis is not None:
            return self.analysis
        return json.dumps(
            {
                "operation": "generate",
                "generation_prompt": "A precise editorial product render",
                "edit_prompt": "A precise editorial product render",
                "preserve": [],
                "quality_checks": ["prompt intent is represented"],
                "confidence": 0.8,
            }
        )

    async def analyze_trade(self, *args, **kwargs):
        return {}

    async def get_tools_response(self, *args, **kwargs):
        return {}

    async def generate_image(self, prompt: str, context=None) -> str:
        self.generate_calls.append(prompt)
        self.generate_context = context
        return "https://cdn.example.com/generated.png"

    async def edit_image(self, prompt: str, image: bytes, mask=None, context=None, image_mime=None, image_filename=None) -> str:
        self.edit_calls.append(
            {
                "prompt": prompt,
                "image": image,
                "mask": mask,
                "context": context,
                "image_mime": image_mime,
                "image_filename": image_filename,
            }
        )
        return "https://cdn.example.com/edited.png"


class FakeMemory:
    def __init__(self):
        self.saved = []

    async def get_context(self, user_id: str):
        return "Paleta principal: negro, blanco y verde lima."

    async def save_interaction(self, user_id: str, data: dict) -> None:
        return None

    async def save_memory(self, category: str, summary: str) -> bool:
        self.saved.append((category, summary))
        return True


class PictureGraphTests(unittest.TestCase):
    def test_decode_request_images_rejects_invalid_base64(self):
        result = _decode_request_images(["not valid base64"])

        self.assertEqual(result["status"], "error")
        self.assertIn("base64 válido", result["message"])

    def test_text_change_with_image_routes_to_edit_image(self):
        async def scenario():
            analysis = json.dumps(
                {
                    "operation": "replace_text",
                    "generation_prompt": "Keep the uploaded poster and change the title text.",
                    "edit_prompt": "Replace only 'Summer Sale' with 'Cyber Week'. Preserve all other design elements.",
                    "target_text": "Summer Sale",
                    "replacement_text": "Cyber Week",
                    "preserve": ["layout", "logo", "colors", "non-target text"],
                    "quality_checks": ["Cyber Week is present", "Summer Sale is absent", "layout is preserved"],
                    "confidence": 0.9,
                }
            )
            llm = FakePictureLLM(analysis=analysis)
            memory = FakeMemory()
            graph = PictureGraph(llm=llm, memory=memory)

            result = await graph.run(
                prompt="cambia el texto Summer Sale por Cyber Week",
                payload={},
                images=[b"image bytes"],
                image_metadata=[{"filename": "poster.jpg", "content_type": "image/jpeg", "size": 123}],
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(len(llm.generate_calls), 0)
            self.assertEqual(len(llm.edit_calls), 1)
            self.assertEqual(llm.edit_calls[0]["image"], b"image bytes")
            self.assertEqual(llm.edit_calls[0]["context"]["operation"], "replace_text")
            self.assertEqual(llm.edit_calls[0]["image_mime"], "image/jpeg")
            self.assertEqual(llm.edit_calls[0]["image_filename"], "poster.jpg")
            self.assertIn("Cyber Week", llm.edit_calls[0]["prompt"])
            self.assertIn("replace_text", result["message"])
            self.assertEqual(memory.saved[0][0], "picture_style")

        asyncio.run(scenario())

    def test_together_generation_adapter_returns_base64_data_url(self):
        class FakeResponse:
            status_code = 200
            text = ""

            def raise_for_status(self):
                return None

            def json(self):
                return {"data": [{"b64_json": "abc123"}]}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.kwargs = kwargs

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, headers=None, json=None):
                self.url = url
                self.headers = headers
                self.payload = json
                return FakeResponse()

        async def scenario():
            adapter = OpenClawLLMAdapter()
            with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=False):
                with patch("httpx.AsyncClient", FakeClient):
                    result = await adapter._generate_image_with_together("poster test")

            self.assertEqual(result, "data:image/png;base64,abc123")

        asyncio.run(scenario())

    def test_generation_without_image_uses_generate_image(self):
        async def scenario():
            llm = FakePictureLLM()
            graph = PictureGraph(llm=llm, memory=FakeMemory())

            result = await graph.run(prompt="un poster editorial minimalista", payload={})

            self.assertEqual(result["status"], "success")
            self.assertEqual(llm.generate_calls, ["A precise editorial product render"])
            self.assertEqual(len(llm.edit_calls), 0)

        asyncio.run(scenario())

    def test_edit_intent_without_image_returns_actionable_error(self):
        async def scenario():
            analysis = json.dumps(
                {
                    "operation": "replace_text",
                    "generation_prompt": "Change the text.",
                    "edit_prompt": "Replace only the requested text.",
                }
            )
            graph = PictureGraph(llm=FakePictureLLM(analysis=analysis), memory=FakeMemory())

            result = await graph.run(prompt="cambia este texto", payload={})

            self.assertEqual(result["status"], "error")
            self.assertIn("requiere una imagen adjunta", result["message"])

        asyncio.run(scenario())

    def test_domain_infers_text_replacement_for_image_prompt(self):
        plan = PictureEditPlan.infer("reemplaza el texto del banner", has_images=True)

        self.assertEqual(plan.operation, PictureOperation.REPLACE_TEXT)
        self.assertIn("Replace only", plan.edit_prompt)
        self.assertIn("layout is preserved", plan.quality_checks)

    def test_base64_image_result_is_returned_structurally_not_in_message(self):
        class Base64LLM(FakePictureLLM):
            async def generate_image(self, prompt: str, context=None) -> str:
                self.generate_calls.append(prompt)
                return "data:image/png;base64,abc123"

        async def scenario():
            result = await PictureGraph(llm=Base64LLM(), memory=FakeMemory()).run(
                prompt="poster minimalista",
                payload={},
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["image_b64"], "abc123")
            self.assertIsNone(result["image_url"])
            self.assertNotIn("abc123", result["message"])

        asyncio.run(scenario())

    def test_free_model_generation_passes_provider_preference(self):
        async def scenario():
            llm = FakePictureLLM()
            result = await PictureGraph(llm=llm, memory=FakeMemory()).run(
                prompt="visual para campaña",
                payload={"prefer_free_model": True, "image_generation_provider": "ollama"},
            )

            self.assertEqual(result["status"], "success")
            self.assertTrue(llm.generate_context["prefer_free_model"])
            self.assertEqual(llm.generate_context["image_generation_provider"], "ollama")

        asyncio.run(scenario())

    def test_base64_edit_result_is_verified(self):
        class VerifiedEditLLM(FakePictureLLM):
            async def edit_image(self, prompt: str, image: bytes, mask=None, context=None, image_mime=None, image_filename=None) -> str:
                self.edit_calls.append({"prompt": prompt, "image": image, "context": context})
                return "data:image/png;base64,aW1hZ2U="

        async def scenario():
            analysis = json.dumps(
                {
                    "operation": "replace_text",
                    "generation_prompt": "Change title text",
                    "edit_prompt": "Replace 'A' with 'B'",
                    "target_text": "A",
                    "replacement_text": "B",
                }
            )
            result = await PictureGraph(llm=VerifiedEditLLM(analysis=analysis), memory=FakeMemory()).run(
                prompt="cambia A por B",
                payload={},
                images=[b"image bytes"],
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["verification"]["status"], "passed")
            self.assertEqual(result["image_b64"], "aW1hZ2U=")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
