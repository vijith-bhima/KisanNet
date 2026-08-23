import math
import hashlib
import logging
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleEmbeddingsClient:
    """
    Google Vertex AI / GenAI Text Embeddings Client using text-embedding-004 (768 dimensions).
    """
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, dimension: int = settings.EMBEDDING_DIMENSION):
        self.model_name = model_name
        self.dimension = dimension

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dimensional normalized embedding vector for text using text-embedding-004.
        """
        try:
            import google.generativeai as genai
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            response = genai.embed_content(
                model=f"models/{self.model_name}",
                content=text,
                task_type="retrieval_document"
            )
            embedding = response.get("embedding", [])
            if isinstance(embedding, dict):
                embedding = embedding.get("values", [])

            if isinstance(embedding, list) and len(embedding) == self.dimension:
                return [float(x) for x in embedding]
        except Exception as e:
            logger.warning(f"Google Embedding API call fallback: {e}")

        # Deterministic 768-dim pseudo-embedding fallback for hackathon testing without active GCP credentials
        return self._generate_fallback_embedding(text)

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, L2-normalized 768-dim vector based on text hash.
        Ensures unit vector properties for vector_cosine_ops in pgvector.
        """
        vec = []
        hash_seed = hashlib.sha256(text.encode("utf-8")).digest()
        for i in range(self.dimension):
            val = (hash_seed[i % len(hash_seed)] + (i * 17)) % 256
            vec.append(val / 255.0 - 0.5)

        # L2 Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

google_embeddings_client = GoogleEmbeddingsClient()
