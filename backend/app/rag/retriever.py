"""Hybrid retriever for job descriptions and skill definitions.

Combines Chroma vector search with SQL prefiltering and a lightweight
keyword re-ranking step.
"""

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Company, Job
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    """Extract English words / numbers / Chinese characters as tokens."""
    if not text:
        return set()
    tokens = re.findall(r"[a-zA-Z0-9+#.]+|[\u4e00-\u9fff]+", text)
    return {t.lower() for t in tokens if len(t) > 1}


def _keyword_score(query: str, document: str, metadata: dict[str, Any]) -> float:
    """Return normalized keyword overlap between query and indexed content."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    parts = [document]
    meta_text = json.dumps(metadata, ensure_ascii=False)
    parts.append(meta_text)
    doc_tokens = _tokenize(" ".join(parts))

    matches = len(query_tokens & doc_tokens)
    return matches / len(query_tokens)


class HybridJobRetriever:
    """Retrieve relevant jobs and skills using vector + SQL + keyword signals."""

    def __init__(self, db: Session):
        self.db = db
        self.vector_store = get_vector_store()

    def _prefilter_job_ids(
        self,
        city: str | None = None,
        industry: str | None = None,
        experience_level: str | None = None,
    ) -> list[int] | None:
        """SQL prefilter on structured Job/Company fields.

        Returns a list of candidate job ids, or None when no filters are given.
        """
        filters_applied = False
        query = self.db.query(Job.id)

        if city:
            query = query.filter(Job.city == city)
            filters_applied = True
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
            filters_applied = True
        if industry:
            query = query.join(Company, Job.company_id == Company.id)
            query = query.filter(Company.industry == industry)
            filters_applied = True

        if not filters_applied:
            return None

        return [row[0] for row in query.all()]

    def _build_job_where(
        self,
        city: str | None = None,
        industry: str | None = None,
        experience_level: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a Chroma metadata filter from SQL-prefiltered job ids."""
        candidate_ids = self._prefilter_job_ids(
            city=city, industry=industry, experience_level=experience_level
        )
        where: dict[str, Any] = {"doc_type": "job"}
        if candidate_ids is not None:
            if not candidate_ids:
                # No SQL candidates -> empty result; use an impossible filter
                return {"$and": [where, {"job_id": {"$in": [-1]}}]}
            where = {"$and": [where, {"job_id": {"$in": candidate_ids}}]}
        return where

    def _rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Combine vector similarity with keyword overlap and return top_k."""
        for candidate in candidates:
            vec_score = candidate.get("score") or 0.0
            kw_score = _keyword_score(
                query, candidate.get("document", ""), candidate.get("metadata", {})
            )
            candidate["keyword_score"] = round(kw_score, 4)
            candidate["hybrid_score"] = round(0.7 * vec_score + 0.3 * kw_score, 4)

        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return candidates[:top_k]

    def search_jobs(
        self,
        query: str,
        city: str | None = None,
        industry: str | None = None,
        experience_level: str | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Hybrid search for job descriptions."""
        where = self._build_job_where(city, industry, experience_level)
        # Retrieve extra candidates so reranking has room to improve ordering
        candidates = self.vector_store.query_similar(
            query=query, filters=where, top_k=max(top_k * 3, 10)
        )
        return self._rerank(query, candidates, top_k)

    def search_skills(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Hybrid search for skill definitions and aliases."""
        where: dict[str, Any] = {"doc_type": "skill"}
        if category:
            where = {"$and": [where, {"category": category}]}
        candidates = self.vector_store.query_similar(
            query=query, filters=where, top_k=max(top_k * 3, 10)
        )
        return self._rerank(query, candidates, top_k)

    def retrieve_for_match(
        self,
        profile_skills: list[str] | str,
        target_job_title: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve reference JDs for the matching agent given a skill profile."""
        if isinstance(profile_skills, str):
            profile_skills = [profile_skills]

        query = " ".join(str(skill) for skill in profile_skills)
        where: dict[str, Any] = {"doc_type": "job"}
        if target_job_title:
            where = {"$and": [where, {"title": target_job_title}]}

        candidates = self.vector_store.query_similar(
            query=query, filters=where, top_k=max(top_k * 3, 10)
        )
        return self._rerank(query, candidates, top_k)
