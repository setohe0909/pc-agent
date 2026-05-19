import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.adapters.open_claw import OpenClawLLMAdapter
from app.main import ActionType, AssistantRequest, Source, _assistant_response
from app.use_cases.model_status import ModelStatusService


class FakeLLM:
    def model_inventory(self) -> dict:
        return {
            "text_cheap": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "status": "configured",
                "detail": "`OPENAI_API_KEY` está configurada.",
            },
            "text_smart": {
                "provider": "openai",
                "model": "gpt-4o",
                "status": "configured",
                "detail": "`OPENAI_API_KEY` está configurada.",
            },
            "image_generation": {
                "provider": "together",
                "model": "black-forest-labs/FLUX.1-schnell-Free",
                "status": "missing_config",
                "detail": "Falta `TOGETHER_API_KEY`.",
            },
            "image_edit": {
                "provider": "openai",
                "model": "openai/gpt-image-1",
                "status": "configured",
                "detail": "`OPENAI_API_KEY` está configurada.",
            },
        }


class ModelStatusTests(unittest.TestCase):
    def test_picture_status_includes_generation_and_edit_models(self):
        result = ModelStatusService(FakeLLM()).get_status("picture")

        self.assertEqual(result["status"], "success")
        self.assertIn("Picture Agent", result["message"])
        self.assertIn("Generación de imagen", result["message"])
        self.assertIn("Edición de imagen", result["message"])
        self.assertEqual(result["model_status"]["agent"], "picture")

    def test_marketer_status_includes_free_model_visuals(self):
        result = ModelStatusService(FakeLLM()).get_status("marketer")

        self.assertIn("Visuales con --free-model", result["message"])
        self.assertIn("TOGETHER_API_KEY", result["message"])

    def test_assistant_response_preserves_model_status_payload(self):
        request = AssistantRequest(
            action_type=ActionType.model_status,
            prompt="picture",
            source=Source(platform="discord"),
            payload={"agent": "picture"},
        )
        response = _assistant_response(
            {
                "status": "success",
                "message": "ok",
                "model_status": {"agent": "picture"},
            },
            request,
        )

        self.assertEqual(response["model_status"], {"agent": "picture"})

    def test_open_claw_inventory_reports_together_missing_key_without_secret_leak(self):
        env = {
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "secret",
            "PICTURE_IMAGE_GENERATION_PROVIDER": "together",
            "TOGETHER_API_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            inventory = OpenClawLLMAdapter().model_inventory()

        self.assertEqual(inventory["image_generation"]["provider"], "together")
        self.assertEqual(inventory["image_generation"]["status"], "missing_config")
        self.assertNotIn("secret", str(inventory))

    def test_open_claw_inventory_redacts_endpoint_credentials(self):
        env = {
            "DEFAULT_LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://user:pass@ollama:11434/path?token=secret",
            "PICTURE_IMAGE_GENERATION_PROVIDER": "ollama",
            "OLLAMA_IMAGE_BASE_URL": "http://user:pass@localhost:11434/path?token=secret",
        }
        with patch.dict(os.environ, env, clear=False):
            inventory = OpenClawLLMAdapter().model_inventory()

        serialized = str(inventory)
        self.assertIn("http://ollama:11434", serialized)
        self.assertIn("http://localhost:11434", serialized)
        self.assertNotIn("user:pass", serialized)
        self.assertNotIn("token=secret", serialized)


if __name__ == "__main__":
    unittest.main()
