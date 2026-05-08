import hashlib
import ipaddress
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from app.supabase_store import KnowledgeSource


@dataclass(frozen=True)
class RawDocument:
    title: str
    content: str
    metadata: dict


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_text(" ".join(self.parts))


async def fetch_source_documents(source: KnowledgeSource, max_documents: int) -> list[RawDocument]:
    if not source.url:
        return []
    response = await fetch_validated_url(source.url)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    body = response.text
    if source.source_type == "rss" or "xml" in content_type or "<rss" in body[:500].lower():
        return parse_rss(body, source, max_documents)
    return [parse_html(body, source)]


async def fetch_validated_url(url: str, max_redirects: int = 3) -> httpx.Response:
    current_url = url
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            validate_fetch_url(current_url)
            response = await client.get(current_url, headers={"User-Agent": "pc-agent-ingestion/0.2.0"})
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response
            location = response.headers.get("location")
            if not location:
                return response
            current_url = urljoin(current_url, location)
        raise RuntimeError("La fuente excedio el limite de redirecciones.")


def parse_rss(body: str, source: KnowledgeSource, max_documents: int) -> list[RawDocument]:
    root = ET.fromstring(body)
    items = root.findall(".//item") or root.findall(".//{*}entry")
    documents: list[RawDocument] = []
    for item in items[:max_documents]:
        title = first_text(item, ["title"]) or source.name
        link = first_text(item, ["link"]) or source.url
        description = first_text(item, ["description", "summary", "content"]) or ""
        documents.append(
            RawDocument(
                title=normalize_text(title),
                content=normalize_text(strip_html(description)),
                metadata={"source_url": source.url, "document_url": link, "source_type": source.source_type},
            )
        )
    return documents


def parse_html(body: str, source: KnowledgeSource) -> RawDocument:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    title = normalize_text(strip_html(title_match.group(1))) if title_match else source.name
    return RawDocument(
        title=title,
        content=strip_html(body),
        metadata={"source_url": source.url, "document_url": source.url, "source_type": source.source_type},
    )


def chunk_document(document: RawDocument, chunk_chars: int) -> list[RawDocument]:
    chunks: list[RawDocument] = []
    paragraphs = [part.strip() for part in document.content.split("\n") if part.strip()]
    current = ""
    for paragraph in paragraphs or [document.content]:
        if len(paragraph) > chunk_chars:
            if current:
                chunks.append(_chunk(document, current, len(chunks)))
                current = ""
            for start in range(0, len(paragraph), chunk_chars):
                chunks.append(_chunk(document, paragraph[start : start + chunk_chars], len(chunks)))
            continue
        if current and len(current) + len(paragraph) + 1 > chunk_chars:
            chunks.append(_chunk(document, current, len(chunks)))
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(_chunk(document, current[:chunk_chars], len(chunks)))
    return chunks


def content_hash(source_id: str, title: str, content: str) -> str:
    digest = hashlib.sha256()
    digest.update(source_id.encode("utf-8"))
    digest.update(title.encode("utf-8"))
    digest.update(content.encode("utf-8"))
    return digest.hexdigest()


def validate_fetch_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("La fuente debe usar http:// o https://")
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local"):
        raise ValueError("No se permiten fuentes locales o privadas.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        raise ValueError("No se permiten fuentes locales o privadas.")


def strip_html(value: str) -> str:
    parser = TextExtractor()
    parser.feed(unescape(value))
    return parser.text()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def first_text(element: ET.Element, names: list[str]) -> str | None:
    for name in names:
        child = element.find(name)
        if child is None:
            child = element.find(f"{{*}}{name}")
        if child is not None and child.text:
            return child.text
    return None


def _chunk(document: RawDocument, content: str, index: int) -> RawDocument:
    metadata = dict(document.metadata)
    metadata["chunk_index"] = index
    return RawDocument(title=document.title, content=content, metadata=metadata)
