import logging
import os
from functools import lru_cache
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model: Any | None = None

    @property
    def model(self):
        if self._model is None:
            # Lazy import to avoid loading torch/sentence-transformers at import time.
            # This speeds up cold starts and keeps the embedding model download
            # isolated until the first encode() call.
            from sentence_transformers import SentenceTransformer

            cache_dir = os.path.join(os.getcwd(), "models_cache")
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Loading embedding model {self.model_name}...")
            # Use a HuggingFace mirror for users in mainland China when the env var is set.
            # If the model is already cached locally, prefer offline loading to avoid
            # unnecessary network requests and SSL errors in restricted networks.
            local_only = _is_model_cached(cache_dir, self.model_name)
            if local_only:
                logger.info("Model found in local cache; loading with local_files_only=True")
            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    cache_folder=cache_dir,
                    local_files_only=local_only,
                )
            except Exception as exc:
                logger.error(
                    "Failed to load embedding model '%s'. If this is the first run, "
                    "ensure you have network access to HuggingFace or set HF_ENDPOINT "
                    "to a local mirror. Error: %s",
                    self.model_name,
                    exc,
                )
                raise
        return self._model

    def encode(self, texts: str | list[str]):

        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

    @property
    def dimension(self) -> int:
        return self.model.get_embedding_dimension()


def _is_model_cached(cache_dir: str, model_name: str) -> bool:
    """Heuristic: check whether the model snapshot already exists locally."""
    normalized = model_name.replace("/", "--")
    model_path = os.path.join(cache_dir, f"models--{normalized}")
    if not os.path.isdir(model_path):
        return False
    # Look for any snapshot directory containing the model weights
    for root, _dirs, files in os.walk(model_path):
        if any(f.endswith((".safetensors", ".bin", ".pt")) for f in files):
            return True
    return False


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
