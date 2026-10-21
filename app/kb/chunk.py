"""Split documents into overlapping chunks for embedding.

Chunking matters more than most people expect: too large and the answer gets
diluted, too small and you lose the context needed to answer. We group
sentences into chunks of roughly `chunk_size` words with `overlap` words of
carry-over so a thought split across two chunks is still recoverable.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol, Sequence

from .load import Document

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


class HasText(Protocol):
    """Anything that carries chunk text — used by the prompt-budget trimmer."""

    @property
    def text(self) -> str: ...


@dataclass
class Chunk:
    """A searchable piece of the knowledge base."""

    id: str
    text: str
    source: str
    section: str | None
    order: int          # position within the source, for stable display

    def citation(self) -> str:
        return f"{self.source} — {self.section}" if self.section else self.source


def _stable_id(source: str, section: str | None, text: str) -> str:
    """Deterministic id so re-indexing does not create duplicates."""
    digest = hashlib.sha1(f"{source}::{section or ''}::{text}".encode("utf-8")).hexdigest()
    return digest[:32]


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[Chunk]:
    """Turn documents into sentence-aligned chunks.

    A document smaller than `chunk_size` becomes a single chunk. Larger ones are
    walked with a sliding window; `overlap` keeps context across the seam.
    """
    if chunk_size <= 0:
        chunk_size = 600
    overlap = max(0, min(overlap, chunk_size // 2))

    chunks: list[Chunk] = []
    for doc in documents:
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(doc.text) if s.strip()]
        if not sentences:
            continue

        # Build sentence groups that fit the budget.
        groups: list[list[str]] = []
        current: list[str] = []
        current_words = 0
        for sentence in sentences:
            words = len(sentence.split())
            if current and current_words + words > chunk_size:
                groups.append(current)
                # carry the tail of the previous group forward
                tail: list[str] = []
                tail_words = 0
                for prev in reversed(current):
                    prev_words = len(prev.split())
                    if tail_words + prev_words > overlap:
                        break
                    tail.insert(0, prev)
                    tail_words += prev_words
                current = tail
                current_words = tail_words
            current.append(sentence)
            current_words += words
        if current:
            groups.append(current)

        for order, group in enumerate(groups):
            body = " ".join(group).strip()
            if not body:
                continue
            # Prepend the section heading: without it, a question that mirrors
            # the heading ("how do I reset my PIN") cannot match its own chunk.
            text = f"{doc.section}. {body}" if doc.section else body
            chunks.append(
                Chunk(
                    id=_stable_id(doc.source, doc.section, text),
                    text=text,
                    source=doc.source,
                    section=doc.section,
                    order=order,
                )
            )

    return chunks


def truncate_for_prompt(chunks: Sequence["HasText"], max_chars: int) -> list["HasText"]:
    """Keep the strongest chunks that still fit the character budget.

    Works with any object exposing a `.text` attribute, so both source chunks
    and retrieved chunks can be trimmed the same way.
    """
    kept: list[HasText] = []
    used = 0
    for chunk in chunks:
        cost = len(chunk.text) + 200  # room for the citation header
        if used + cost > max_chars:
            continue
        kept.append(chunk)
        used += cost
    return kept
