import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import _extract_post_suggestion, _is_requests_channel


class MarketerApprovalTests(unittest.TestCase):
    def test_accepts_commands_when_requests_channel_is_not_configured(self):
        import os

        previous = os.environ.pop("DISCORD_REQUESTS_CHANNEL_ID", None)
        try:
            self.assertTrue(_is_requests_channel(12345))
        finally:
            if previous is not None:
                os.environ["DISCORD_REQUESTS_CHANNEL_ID"] = previous

    def test_restricts_commands_when_requests_channel_is_configured(self):
        import os

        previous = os.environ.get("DISCORD_REQUESTS_CHANNEL_ID")
        os.environ["DISCORD_REQUESTS_CHANNEL_ID"] = "12345"
        try:
            self.assertTrue(_is_requests_channel(12345))
            self.assertFalse(_is_requests_channel(99999))
        finally:
            if previous is None:
                os.environ.pop("DISCORD_REQUESTS_CHANNEL_ID", None)
            else:
                os.environ["DISCORD_REQUESTS_CHANNEL_ID"] = previous

    def test_extracts_approved_post_suggestion_from_message_fallback(self):
        message = (
            "📝 **Sugerencia de publicación para instagram:**\n\n"
            "¡Descubre la magia de los Andes! 🏔️✨ Sumérgete en paisajes impresionantes.\n\n"
            "**Hashtags:** #Andes #Aventura #Paisajes #Viajes #Naturaleza"
        )

        suggestion = _extract_post_suggestion(message)

        self.assertEqual(
            suggestion,
            {
                "enhanced_description": "¡Descubre la magia de los Andes! 🏔️✨ Sumérgete en paisajes impresionantes.",
                "hashtags": ["#Andes", "#Aventura", "#Paisajes", "#Viajes", "#Naturaleza"],
                "caption": "¡Descubre la magia de los Andes! 🏔️✨ Sumérgete en paisajes impresionantes.\n\n#Andes #Aventura #Paisajes #Viajes #Naturaleza",
            },
        )


if __name__ == "__main__":
    unittest.main()
