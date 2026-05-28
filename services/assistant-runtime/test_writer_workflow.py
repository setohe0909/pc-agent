import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.use_cases.writer_workflow import WriterWorkflow


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def chat(self, prompt: str, **kwargs):
        self.calls.append((prompt, kwargs))
        if "palabras clave" in prompt.lower():
            return "minimalist, studio"
        return "# Titulo Editorial\n\nContenido listo para publicar."


class FakeMemory:
    def __init__(self, context: str = "Voz de marca: clara, premium y directa."):
        self.context = context
        self.interactions = []

    async def get_context(self, user_id: str):
        return self.context

    async def save_interaction(self, user_id: str, data: dict) -> None:
        self.interactions.append((user_id, data))

    async def save_memory(self, category: str, summary: str) -> bool:
        return True


class WriterWorkflowTests(unittest.TestCase):
    def setUp(self):
        self._old_obsidian = os.environ.get("OBSIDIAN_VAULT_PATH")

    def tearDown(self):
        if self._old_obsidian is None:
            os.environ.pop("OBSIDIAN_VAULT_PATH", None)
        else:
            os.environ["OBSIDIAN_VAULT_PATH"] = self._old_obsidian

    def test_chat_uses_prompt_and_records_interaction(self):
        async def scenario():
            llm = FakeLLM()
            memory = FakeMemory()
            workflow = WriterWorkflow(llm, memory)

            result = await workflow.execute_writer_action("Escribe un hook", {"sub_command": "chat"})

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["command"], "chat")
            self.assertEqual(llm.calls[0][0], "Escribe un hook")
            self.assertIn("system_instruction", llm.calls[0][1])
            self.assertEqual(memory.interactions[0][0], "writer")

        asyncio.run(scenario())

    def test_blog_saves_markdown_with_structured_result(self):
        async def scenario():
            with tempfile.TemporaryDirectory() as tmp:
                os.environ["OBSIDIAN_VAULT_PATH"] = tmp
                workflow = WriterWorkflow(FakeLLM(), FakeMemory())

                result = await workflow.execute_writer_action("Lanzamiento", {"sub_command": "blog", "language": "es"})

                self.assertEqual(result["status"], "success")
                self.assertEqual(result["command"], "blog")
                self.assertTrue(result["artifact"].startswith("Blog/"))
                self.assertNotIn("source.unsplash.com", result["content"])
                saved_path = Path(tmp) / result["artifact"]
                self.assertTrue(saved_path.exists())
                self.assertIn("Contenido listo", saved_path.read_text(encoding="utf-8"))
                self.assertEqual(saved_path.stat().st_mode & 0o777, 0o664)
                self.assertEqual(saved_path.parent.stat().st_mode & 0o777, 0o775)

        asyncio.run(scenario())

    def test_persistence_failure_returns_error_not_success(self):
        async def scenario():
            os.environ["OBSIDIAN_VAULT_PATH"] = "/dev/null"
            workflow = WriterWorkflow(FakeLLM(), FakeMemory())

            result = await workflow.execute_writer_action("Lanzamiento", {"sub_command": "storytelling"})

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["code"], "writer.persistence_failed")
            self.assertIn("content", result)

        asyncio.run(scenario())

    def test_rejects_empty_or_unknown_requests(self):
        async def scenario():
            workflow = WriterWorkflow(FakeLLM(), FakeMemory())

            empty = await workflow.execute_writer_action("", {"sub_command": "chat"})
            unknown = await workflow.execute_writer_action("Tema", {"sub_command": "publish"})

            self.assertEqual(empty["code"], "writer.empty_prompt")
            self.assertEqual(unknown["code"], "writer.unsupported_action")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
