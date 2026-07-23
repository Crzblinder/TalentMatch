"""Qdrant 向量存储适配器。"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import get_settings
from app.rag.vector_store_base import VectorStoreBase

logger = logging.getLogger(__name__)


def _get_embedding_model():
    """延迟加载 embedding 模型。"""
    from app.rag.embeddings import get_embedding_model

    return get_embedding_model()


class QdrantVectorStore(VectorStoreBase):
    """远程 Qdrant 向量存储实现，支持多实例共享同一集群。"""

    def __init__(self, collection_name: str):
        settings = get_settings()
        self.collection_name = collection_name
        self.url = settings.qdrant_url

        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise ImportError(
                "Qdrant client is required. Install it with: pip install qdrant-client"
            ) from exc

        self.client = QdrantClient(url=self.url)
        self._ensure_collection()

    def _vector_size(self) -> int:
        """通过一次空文本编码获取向量维度。"""
        sample = _get_embedding_model().encode(["sample"])
        if hasattr(sample, "shape"):
            return int(sample.shape[-1])
        return len(sample[0])

    def _ensure_collection(self) -> None:
        """若集合不存在则创建，使用 cosine 距离。"""
        from qdrant_client.models import Distance, VectorParams

        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            vector_size = self._vector_size()
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Qdrant 集合已创建: %s (dim=%d)", self.collection_name, vector_size)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = _get_embedding_model().encode(texts)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return list(embeddings)

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        if metadatas is None:
            metadatas = [{} for _ in ids]

        from qdrant_client.models import PointStruct

        embeddings = self._embed(documents)
        points = []
        for idx, doc_id in enumerate(ids):
            payload = dict(metadatas[idx])
            payload["document"] = documents[idx]
            # Qdrant payload 只接受可 JSON 序列化的标量/列表
            for k, v in list(payload.items()):
                if isinstance(v, dict):
                    payload[k] = json.dumps(v, ensure_ascii=False)
            points.append(
                PointStruct(id=doc_id, vector=embeddings[idx], payload=payload)
            )

        self.client.upsert(collection_name=self.collection_name, points=points)

    def query(
        self,
        query_texts: list[str],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        embeddings = self._embed(query_texts)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embeddings[0],
            limit=n_results,
            with_payload=True,
            query_filter=self._build_filter(where),
        )
        return {"results": results}

    def _build_filter(self, where: dict[str, Any] | None):
        """将简单 where 条件转换为 Qdrant Filter。"""
        if not where:
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        conditions = []
        for key, value in where.items():
            conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )
        return Filter(must=conditions) if conditions else None

    def delete_all(self) -> None:
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()

    def add_job_documents(self, jobs: list[Any]) -> int:
        if not jobs:
            return 0

        ids = []
        documents = []
        metadatas = []
        for job in jobs:
            company_name = job.company.name if job.company else ""
            required_skills = job.required_skills
            if isinstance(required_skills, str):
                try:
                    required_skills = json.loads(required_skills)
                except json.JSONDecodeError:
                    required_skills = []
            ids.append(f"job:{job.id}")
            documents.append(job.description or "")
            metadatas.append({
                "job_id": job.id,
                "title": job.title or "",
                "company": company_name,
                "required_skills": required_skills,
                "doc_type": "job",
            })

        self.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(jobs)

    def add_skill_documents(self, skills: list[Any]) -> int:
        if not skills:
            return 0

        ids = []
        documents = []
        metadatas = []
        for skill in skills:
            aliases = skill.aliases
            if isinstance(aliases, str):
                try:
                    aliases = json.loads(aliases)
                except json.JSONDecodeError:
                    aliases = []
            text_parts = [skill.definition or ""]
            if aliases:
                text_parts.append("别名：" + "、".join(str(a) for a in aliases))

            ids.append(f"skill:{skill.id}")
            documents.append("\n".join(text_parts))
            metadatas.append({
                "skill_id": skill.id,
                "name": skill.name or "",
                "category": skill.category or "",
                "doc_type": "skill",
            })

        self.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(skills)

    def query_similar(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        embeddings = self._embed([query])
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embeddings[0],
            limit=top_k,
            with_payload=True,
            query_filter=self._build_filter(filters),
        )

        output: list[dict[str, Any]] = []
        for point in results:
            payload = dict(point.payload or {})
            document = payload.pop("document", "")
            score = round(float(point.score), 4) if point.score is not None else None
            output.append({
                "id": point.id,
                "document": document,
                "metadata": payload,
                "score": score,
                "source": "qdrant",
            })
        return output

    def clear_collection(self) -> None:
        self.delete_all()
