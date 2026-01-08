"""Embedding generation using OpenRouter API."""

import logging
from dataclasses import dataclass, field

import httpx

from bark.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingGenerator:
    """Generates embeddings using OpenRouter's embedding API."""

    settings: Settings = field(default_factory=get_settings)
    _client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.openrouter_base_url,
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        result = await self.embed_batch([text])
        return result[0] if result else []

    async def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        client = await self._get_client()
        all_embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            payload = {
                "model": self.settings.embedding_model,
                "input": batch,
            }

            try:
                response = await client.post("/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()

                # Extract embeddings from response
                for item in data.get("data", []):
                    all_embeddings.append(item["embedding"])

            except httpx.HTTPStatusError as e:
                logger.error(f"Embedding API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
                raise

        return all_embeddings

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instance
_generator: EmbeddingGenerator | None = None


async def get_embedding_generator() -> EmbeddingGenerator:
    """Get the global embedding generator instance."""
    global _generator
    if _generator is None:
        _generator = EmbeddingGenerator()
    return _generator
