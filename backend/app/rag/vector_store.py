import json
import logging
import os
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)


class _ProjectEmbeddingFunction:
    """ChromaDB-compatible embedding function backed by the project's EmbeddingModel.

    Avoids downloading ChromaDB's default ONNX model from AWS S3 (very slow in China).
    Uses BAAI/bge-small-zh-v1.5 via sentence-transformers instead.
    """

    def __init__(self) -> None:
        self._model = None

    def name(self) -> str:
        """Return a stable name for ChromaDB 1.5+ compatibility."""
        return "project_bge_small_zh_v1_5"

    def is_legacy(self) -> bool:
        """Declare this as a non-legacy embedding function."""
        return False

    def _get_model(self):
        if self._model is None:
            from app.rag.embeddings import get_embedding_model

            self._model = get_embedding_model()
        return self._model

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self._get_model().encode(input)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return list(embeddings)


# Module-level singleton so all collections share the same model instance
_default_ef = _ProjectEmbeddingFunction()


class VectorStore:
    def __init__(self, collection_name: str):
        settings = get_settings()
        self.collection_name = collection_name
        self.path = settings.vector_db_path
        os.makedirs(self.path, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # 手动计算 embeddings 传入 Chroma，避免自定义 EmbeddingFunction 的兼容性问题
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ):
        if metadatas is None:
            metadatas = [{} for _ in ids]
        # Chroma requires metadata values to be primitive types
        clean_metadatas = []
        for m in metadatas:
            clean = {}
            for k, v in m.items():
                if isinstance(v, (list, dict)):
                    clean[k] = str(v)
                else:
                    clean[k] = v
            clean_metadatas.append(clean)
        embeddings = _default_ef(documents)
        self.collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=clean_metadatas
        )

    def query(
        self,
        query_texts: list[str],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ):
        embeddings = _default_ef(query_texts)
        kwargs: dict[str, Any] = {
            "query_embeddings": embeddings,
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        return self.collection.query(**kwargs)

    def delete_all(self):
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_job_documents(self, jobs: list[Any]) -> int:
        """Index Job.description into the vector store.

        Metadata includes: job_id, title, company, required_skills.
        """
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
        """Index Skill.definition and aliases into the vector store.

        Metadata includes: skill_id, name, category.
        """
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
        """Return a list of similar documents with score and source metadata."""
        results = self.query(
            query_texts=[query],
            n_results=top_k,
            where=filters,
        )
        output: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []
        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []

        for idx, doc_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = distances[idx] if idx < len(distances) else None
            # Chroma cosine distance -> similarity score
            score = round(1.0 - float(distance), 4) if distance is not None else None
            output.append({
                "id": doc_id,
                "document": documents[idx] if idx < len(documents) else "",
                "metadata": metadata,
                "score": score,
                "source": "chroma",
            })
        return output

    def clear_collection(self) -> None:
        """Reset the collection by deleting and recreating it."""
        self.delete_all()


# Module-level singleton for the project collection
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Return the singleton vector store for job graph knowledge."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore("job_graph_knowledge")
    return _vector_store
