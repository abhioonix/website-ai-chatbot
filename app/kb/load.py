"""Load raw documents from a knowledge-base directory.

Supported inputs (mixed freely in one folder):
  *.md, *.txt   plain prose; markdown headings become section names
  *.json        either a list of {"question","answer"} FAQ pairs, or
                a list of {"title","content"}, or a list of {"source","text"}
  *.pdf         needs the optional `pypdf` package

Every document carries the name of the file it came from so answers can cite it.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("chatbot.kb.load")

SUPPORTED_SUFFIXES = {".md", ".txt", ".json", ".pdf"}


@dataclass
class Document:
    """A unit of source material."""

    source: str            # file name, e.g. "vaanilink-faq.md"
    text: str
    section: str | None = None
    meta: dict = field(default_factory=dict)

    def citation(self) -> str:
        if self.section:
            return f"{self.source} — {self.section}"
        return self.source


def _split_markdown_sections(text: str) -> list[tuple[str | None, str]]:
    """Split markdown into (heading, body) pairs."""
    lines = text.splitlines()
    sections: list[tuple[str | None, list[str]]] = []
    current_heading: str | None = None
    buffer: list[str] = []

    for line in lines:
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            if buffer:
                sections.append((current_heading, buffer))
                buffer = []
            current_heading = heading.group(2).strip()
        else:
            buffer.append(line)
    if buffer:
        sections.append((current_heading, buffer))

    out: list[tuple[str | None, str]] = []
    for heading, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if body:
            out.append((heading, body))
    return out or [(None, text.strip())]


def _load_text_file(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [
        Document(source=path.name, text=body, section=heading)
        for heading, body in _split_markdown_sections(text)
    ]


def _load_json_file(path: Path) -> list[Document]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))

    if isinstance(data, dict):
        data = data.get("documents") or data.get("entries") or data.get("faqs") or []
    if not isinstance(data, list):
        logger.warning("Skipping %s: expected a JSON list", path.name)
        return []

    docs: list[Document] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or item.get("title") or "").strip()
        answer = str(item.get("answer") or item.get("content") or item.get("text") or "").strip()
        source = str(item.get("source") or path.name).strip()

        if question and answer:
            # FAQ pair — keep the question attached so it is searchable.
            docs.append(Document(source=source, text=f"Q: {question}\nA: {answer}", section=question))
        elif answer:
            docs.append(Document(source=source, text=answer, section=str(item.get("section") or None)))
        else:
            logger.warning("Skipping entry %d in %s: no usable text", i, path.name)
    return docs


def _load_pdf_file(path: Path) -> list[Document]:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("PDF support needs `pypdf`. Skipping %s.", path.name)
        return []

    reader = PdfReader(str(path))
    docs: list[Document] = []
    for i, page in enumerate(reader.pages, start=1):
        body = (page.extract_text() or "").strip()
        if body:
            docs.append(Document(source=path.name, text=body, section=f"page {i}"))
    return docs


def load_documents(source_dir: str | Path) -> list[Document]:
    """Read every supported file in a directory (non-recursive)."""
    root = Path(source_dir)
    if not root.is_dir():
        logger.warning("Knowledge base directory not found: %s", root)
        return []

    docs: list[Document] = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            if path.suffix.lower() == ".json":
                docs.extend(_load_json_file(path))
            elif path.suffix.lower() == ".pdf":
                docs.extend(_load_pdf_file(path))
            else:
                docs.extend(_load_text_file(path))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load %s: %s", path.name, exc)

    logger.info("Loaded %d documents from %s", len(docs), root)
    return docs
