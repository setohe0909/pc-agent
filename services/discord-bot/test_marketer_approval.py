import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import _extract_post_suggestion


class MarketerApprovalTests(unittest.TestCase):
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
