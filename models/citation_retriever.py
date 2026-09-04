"""
Retrieval-augmented citation engine, replacing the naive keyword-substring
branch matching previously used to pick a "scientific citation" for a
user's free-text query in models/odin_ai.py's process_query().

TF-IDF + cosine similarity (scikit-learn) is the PRIMARY retrieval path.
For a corpus of a few dozen short, keyword-dense citation entries, sparse
lexical matching is deterministic, has zero latency, has no external
failure mode during a live demo, and is trivially unit-testable against an
exact expected ranking - dense embeddings buy little over sparse lexical
matching at this corpus size. Fitting a TfidfVectorizer over ~40 short
strings is sub-millisecond, so there is no separate "training" step here;
it's fit once at process startup (see get_default_retriever()).

An optional secondary/upgrade tier calls Hugging Face's hosted
feature-extraction endpoint for dense embeddings (the same httpx-to-router
pattern models/odin_ai.py already uses for chat) - this demonstrates
knowing when NOT to reach for the heavier tool, mirroring
models/anomaly_detector.py's MAD-vs-IsolationForest choice. It requires an
HF API key and is never the default.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional

CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "citations_corpus.json")


@dataclass
class Citation:
    id: str
    topic_tags: List[str]
    title: str
    authors: str
    year: int
    journal: str
    doi_or_url: str
    finding_summary: str

    def to_response_dict(self) -> dict:
        """Matches the shape models/odin_ai.py's old SCIENTIFIC_CITATIONS entries had, for API compatibility."""
        return {
            "title": self.title,
            "authors": self.authors,
            "journal": f"{self.journal} ({self.year})",
            "key_takeaway": self.finding_summary,
        }


def load_corpus(path: str = CORPUS_PATH) -> List[Citation]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Citation(**entry) for entry in raw]


def _citation_text(c: Citation) -> str:
    """Text representation TF-IDF is fit against - title, tags, and the finding summary carry the most retrieval signal."""
    return f"{c.title} {' '.join(c.topic_tags)} {c.finding_summary}"


class TfidfCitationRetriever:
    """Primary retrieval path: sparse lexical matching over the citation corpus."""

    def __init__(self, corpus: List[Citation]):
        from sklearn.feature_extraction.text import TfidfVectorizer

        if not corpus:
            raise ValueError("Citation corpus is empty")
        self.corpus = corpus
        # Word-level tokens, not character n-grams. Character 3-5grams were
        # tried and tested empirically: they fix a real gap (a query about
        # "mitochondria" scores 0 overlap against corpus text about
        # "mitochondrial biogenesis" under word-level matching - different
        # tokens, no stemmer in play), but they also dilute precision on
        # longer, more generic queries - a "recovery score" query started
        # ranking an overtraining-injury paper above the actually-relevant
        # HRV/recovery paper, because common substrings like "training"
        # overlap heavily across many unrelated corpus entries. That's a
        # worse regression than the gap it fixes, so word-level tokens are
        # kept as the default. Known limitation: queries using a
        # morphological variant of a corpus term (e.g. "mitochondria" vs.
        # "mitochondrial") may not retrieve that entry - the honest fix
        # would be a real stemmer/lemmatizer, not a n-gram-width workaround.
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform([_citation_text(c) for c in corpus])

    def retrieve(self, query: str, top_k: int = 2) -> List[Citation]:
        from sklearn.metrics.pairwise import cosine_similarity

        if not query.strip():
            return []
        query_vector = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self._matrix)[0]
        ranked_indices = similarities.argsort()[::-1]
        return [self.corpus[i] for i in ranked_indices[:top_k] if similarities[i] > 0.0]


class HFEmbeddingCitationRetriever:
    """
    Optional secondary/upgrade tier: dense embeddings via Hugging Face's
    hosted feature-extraction endpoint. No local torch/sentence-transformers
    dependency, consistent with this project's lightweight Quick Start.
    Only used when the caller has an HF API key; TfidfCitationRetriever
    remains the default with no external dependency or failure mode.
    """

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_URL = f"https://router.huggingface.co/hf-inference/models/{EMBEDDING_MODEL}/pipeline/feature-extraction"

    def __init__(self, corpus: List[Citation]):
        self.corpus = corpus
        self._embeddings = None  # populated lazily on first retrieve() call

    async def _embed(self, texts: List[str], api_key: str):
        import httpx
        import numpy as np

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(self.EMBEDDING_URL, headers=headers, json={"inputs": texts})
            resp.raise_for_status()
            return np.array(resp.json())

    async def retrieve(self, query: str, api_key: str, top_k: int = 2) -> List[Citation]:
        import numpy as np

        if self._embeddings is None:
            self._embeddings = await self._embed([_citation_text(c) for c in self.corpus], api_key)
        query_embedding = (await self._embed([query], api_key))[0]

        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_embedding)
        norms[norms == 0] = 1e-9
        similarities = (self._embeddings @ query_embedding) / norms
        ranked_indices = similarities.argsort()[::-1]
        return [self.corpus[i] for i in ranked_indices[:top_k]]


@lru_cache(maxsize=1)
def get_default_retriever() -> TfidfCitationRetriever:
    return TfidfCitationRetriever(load_corpus())


async def retrieve_citations(query: str, top_k: int = 2, hf_api_key: Optional[str] = None) -> List[Citation]:
    """
    Facade used by models/odin_ai.py. Tries the HF embedding tier only if a
    key is supplied, falling back to TF-IDF on any failure - mirroring the
    live-LLM/heuristic-fallback pattern already used for chat generation.
    """
    if hf_api_key:
        try:
            embedding_retriever = HFEmbeddingCitationRetriever(load_corpus())
            results = await embedding_retriever.retrieve(query, api_key=hf_api_key, top_k=top_k)
            if results:
                return results
        except Exception:
            pass  # fall through to TF-IDF
    return get_default_retriever().retrieve(query, top_k=top_k)
