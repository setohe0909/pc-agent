import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "ingestion-worker"))

from app.content import RawDocument, chunk_document, content_hash, parse_rss, strip_html, validate_fetch_url
from app.supabase_store import KnowledgeSource, _format_vector


class IngestionWorkerTests(unittest.TestCase):
    def test_content_hash_is_stable(self) -> None:
        first = content_hash("source", "title", "content")
        second = content_hash("source", "title", "content")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_strip_html_ignores_script_content(self) -> None:
        text = strip_html("<html><script>alert('x')</script><h1>Titulo</h1><p>Contenido</p></html>")

        self.assertEqual(text, "Titulo Contenido")

    def test_parse_rss_items(self) -> None:
        source = KnowledgeSource(
            id="source",
            name="RSS",
            source_type="rss",
            url="https://example.com/rss.xml",
            schedule=None,
            enabled=True,
        )
        rss = """
        <rss><channel><item>
          <title>Mercado</title>
          <link>https://example.com/market</link>
          <description><![CDATA[<p>Probabilidad sube</p>]]></description>
        </item></channel></rss>
        """

        documents = parse_rss(rss, source, max_documents=5)

        self.assertEqual(documents[0].title, "Mercado")
        self.assertEqual(documents[0].content, "Probabilidad sube")
        self.assertEqual(documents[0].metadata["document_url"], "https://example.com/market")

    def test_chunk_document_adds_chunk_index(self) -> None:
        chunks = chunk_document(
            RawDocument(title="T", content="uno\n\ndos tres", metadata={"source_url": "x"}),
            chunk_chars=5,
        )

        self.assertEqual([chunk.metadata["chunk_index"] for chunk in chunks], [0, 1, 2])

    def test_chunk_document_preserves_long_paragraphs(self) -> None:
        chunks = chunk_document(RawDocument(title="T", content="abcdef", metadata={}), chunk_chars=2)

        self.assertEqual([chunk.content for chunk in chunks], ["ab", "cd", "ef"])

    def test_validate_fetch_url_rejects_localhost(self) -> None:
        with self.assertRaises(ValueError):
            validate_fetch_url("http://127.0.0.1:8000/private")

    def test_format_vector_for_pgvector(self) -> None:
        self.assertEqual(_format_vector([1, 0.5, -0.25]), "[1.00000000,0.50000000,-0.25000000]")


if __name__ == "__main__":
    unittest.main()
