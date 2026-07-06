"""
CareerLift AI — RAG (Retrieval-Augmented Generation) Module
Chunks, indexes, and retrieves relevant knowledge base content.
"""

import os
import json
import math
import re
from typing import List, Tuple, Dict, Any
from pathlib import Path

# Optionally use numpy for faster cosine similarity
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"


# ---------------------------------------------------------------------------
# Simple TF-IDF-style vector retrieval (no external embedding API required)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split into tokens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    tf: Dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    total = len(tokens) or 1
    return {k: v / total for k, v in tf.items()}


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    common_keys = set(vec_a) & set(vec_b)
    if not common_keys:
        return 0.0
    dot   = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Knowledge Base Loader
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """Loads all .json / .txt knowledge base files and builds an in-memory index."""

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if not KNOWLEDGE_BASE_DIR.exists():
            print(f"[RAG] Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
            return

        for fpath in KNOWLEDGE_BASE_DIR.rglob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        self._add_chunk(item, source=fpath.name)
                elif isinstance(data, dict):
                    self._add_chunk(data, source=fpath.name)
            except Exception as exc:
                print(f"[RAG] Error loading {fpath}: {exc}")

        for fpath in KNOWLEDGE_BASE_DIR.rglob("*.txt"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    text = f.read()
                self._chunk_text(text, source=fpath.name)
            except Exception as exc:
                print(f"[RAG] Error loading {fpath}: {exc}")

        print(f"[RAG] Loaded {len(self.chunks)} chunks from knowledge base.")

    def _add_chunk(self, item: Dict, source: str):
        """Add a structured knowledge item as a chunk."""
        text_parts = []
        for field in ("question", "answer", "tip", "content", "text", "title", "description"):
            if field in item and item[field]:
                text_parts.append(str(item[field]))
        text = " ".join(text_parts)
        if text.strip():
            self.chunks.append({
                "text":     text,
                "source":   source,
                "metadata": item,
                "tokens":   tokenize(text),
                "tf":       compute_tf(tokenize(text)),
            })

    def _chunk_text(self, text: str, source: str, chunk_size: int = 500, overlap: int = 50):
        """Split a plain-text file into overlapping chunks."""
        words = text.split()
        i = 0
        while i < len(words):
            chunk_words = words[i: i + chunk_size]
            chunk_text = " ".join(chunk_words)
            tokens = tokenize(chunk_text)
            self.chunks.append({
                "text":     chunk_text,
                "source":   source,
                "metadata": {},
                "tokens":   tokens,
                "tf":       compute_tf(tokens),
            })
            i += chunk_size - overlap

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.05) -> List[Dict]:
        """Return top_k most relevant chunks for the given query."""
        if not self.chunks:
            return []
        query_tokens = tokenize(query)
        query_tf = compute_tf(query_tokens)
        scored = []
        for chunk in self.chunks:
            score = cosine_similarity(query_tf, chunk["tf"])
            if score >= threshold:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into a context string for the LLM prompt."""
        if not chunks:
            return ""
        parts = ["### Relevant Knowledge Base Context\n"]
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "knowledge_base")
            meta   = chunk.get("metadata", {})
            category = meta.get("category", meta.get("type", "general"))
            parts.append(f"**[{i}] Source: {source} | Category: {category}**")
            parts.append(chunk["text"].strip())
            parts.append("")
        return "\n".join(parts)


# Module-level singleton
_kb: KnowledgeBase = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb


def retrieve_context(query: str, top_k: int = 5) -> str:
    """Public helper — retrieve and format context for a query."""
    kb = get_knowledge_base()
    chunks = kb.retrieve(query, top_k=top_k)
    return kb.format_context(chunks)


def augmented_prompt(user_query: str, system_prompt: str, top_k: int = 5) -> Tuple[str, str]:
    """
    Build a RAG-augmented (system_prompt, user_prompt) pair.
    Returns (augmented_system_prompt, user_query).
    """
    context = retrieve_context(user_query, top_k=top_k)
    if context:
        augmented_system = f"{system_prompt}\n\n{context}"
    else:
        augmented_system = system_prompt
    return augmented_system, user_query
