import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "assistant-runtime"))

from app.adapters.pilot_web import _safe_branch_name, _safe_repo_path
from app.use_cases.coder_web_package import validate_generated_files


class CoderWebProductionTests(unittest.TestCase):
    def test_generated_package_requires_package_json(self) -> None:
        with self.assertRaises(ValueError):
            validate_generated_files([{"path": "src/App.tsx", "content": "export default function App() { return null }"}])

    def test_generated_package_accepts_buildable_manifest(self) -> None:
        files = validate_generated_files(
            [
                {"path": "package.json", "content": '{"scripts":{"build":"vite"}}'},
                {"path": "src/App.tsx", "content": "export default function App() { return null }"},
            ]
        )

        self.assertEqual(len(files), 2)

    def test_repo_paths_reject_traversal(self) -> None:
        with self.assertRaises(RuntimeError):
            _safe_repo_path("../secret")

    def test_branch_names_are_sanitized(self) -> None:
        self.assertEqual(_safe_branch_name("Coder Web: Nueva tienda"), "Coder-Web-Nueva-tienda")


if __name__ == "__main__":
    unittest.main()
