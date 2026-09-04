"""
Unit tests for models/citation_retriever.py - TF-IDF retrieval is
deterministic, so these assert exact expected rankings, not just "returns
something". Uses a small hand-built corpus rather than the real
data/citations_corpus.json so the expected ranking is unambiguous and
doesn't drift as the real corpus grows.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from models.citation_retriever import Citation, TfidfCitationRetriever, retrieve_citations


def _toy_corpus():
    return [
        Citation(
            id="hrv_paper", topic_tags=["hrv", "recovery"],
            title="Heart Rate Variability and Autonomic Recovery",
            authors="Test, A.", year=2020, journal="Journal of HRV",
            doi_or_url="https://example.com/hrv", finding_summary="HRV reflects parasympathetic recovery status.",
        ),
        Citation(
            id="sleep_paper", topic_tags=["sleep"],
            title="Deep Sleep and Cognitive Restoration",
            authors="Test, B.", year=2021, journal="Journal of Sleep",
            doi_or_url="https://example.com/sleep", finding_summary="Deep sleep supports memory consolidation.",
        ),
        Citation(
            id="glucose_paper", topic_tags=["glucose", "cgm"],
            title="Glycemic Variability and Time in Range",
            authors="Test, C.", year=2019, journal="Journal of Metabolism",
            doi_or_url="https://example.com/glucose", finding_summary="Time-in-range predicts metabolic health outcomes.",
        ),
    ]


def test_tfidf_retriever_ranks_relevant_citation_first():
    retriever = TfidfCitationRetriever(_toy_corpus())
    results = retriever.retrieve("How is my heart rate variability affecting my recovery?", top_k=1)
    assert len(results) == 1
    assert results[0].id == "hrv_paper"


def test_tfidf_retriever_distinguishes_unrelated_topics():
    retriever = TfidfCitationRetriever(_toy_corpus())
    sleep_results = retriever.retrieve("Tell me about deep sleep and memory", top_k=1)
    glucose_results = retriever.retrieve("What does my glucose time in range mean?", top_k=1)
    assert sleep_results[0].id == "sleep_paper"
    assert glucose_results[0].id == "glucose_paper"


def test_tfidf_retriever_empty_query_returns_nothing():
    retriever = TfidfCitationRetriever(_toy_corpus())
    assert retriever.retrieve("", top_k=2) == []


def test_tfidf_retriever_respects_top_k():
    retriever = TfidfCitationRetriever(_toy_corpus())
    results = retriever.retrieve("health metrics", top_k=2)
    assert len(results) <= 2


def test_citation_to_response_dict_shape():
    citation = _toy_corpus()[0]
    d = citation.to_response_dict()
    assert set(d.keys()) == {"title", "authors", "journal", "key_takeaway"}
    assert "2020" in d["journal"]


def test_retrieve_citations_falls_back_to_tfidf_without_hf_key():
    results = asyncio.run(retrieve_citations("How is my recovery today?", top_k=2, hf_api_key=None))
    assert len(results) > 0


def test_retrieve_citations_falls_back_on_hf_failure():
    # Mock the network call rather than hitting HF for real with a bad key -
    # keeps this test fast and independent of network availability, while
    # still verifying the facade catches a failure and falls back to TF-IDF
    # rather than raising or returning nothing.
    with patch(
        "models.citation_retriever.HFEmbeddingCitationRetriever.retrieve",
        new=AsyncMock(side_effect=RuntimeError("simulated HF outage")),
    ):
        results = asyncio.run(retrieve_citations("How is my recovery today?", top_k=2, hf_api_key="hf_some_key"))
    assert len(results) > 0
