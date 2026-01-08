"""Summarizer for compressing wiki content before embedding."""

import logging
from dataclasses import dataclass, field

import httpx

from bark.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """Summarize the following wiki content in 1-2 sentences that capture the key topics and information. 
Focus on what someone searching for this content would want to find.
Keep the summary concise and searchable.

Content:
{content}

Summary:"""


@dataclass
class Summarizer:
    """Generates summaries using a cheap LLM for embedding optimization."""

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

    async def summarize(self, content: str) -> str:
        """Generate a summary for a single piece of content.

        Args:
            content: Content to summarize

        Returns:
            Summary text
        """
        if not content.strip():
            return ""

        client = await self._get_client()

        payload = {
            "model": self.settings.summarization_model,
            "messages": [
                {"role": "user", "content": SUMMARIZE_PROMPT.format(content=content)}
            ],
            "max_tokens": 150,
            "temperature": 0.3,
        }

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            summary = data["choices"][0]["message"]["content"].strip()
            return summary
        except httpx.HTTPStatusError as e:
            logger.error(f"Summarization API error: {e.response.status_code} - {e.response.text}")
            # Fall back to truncated original content
            return content[:200] if len(content) > 200 else content
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return content[:200] if len(content) > 200 else content

    async def summarize_batch(self, contents: list[str]) -> list[str]:
        """Generate summaries for multiple pieces of content.

        Args:
            contents: List of content to summarize

        Returns:
            List of summaries
        """
        summaries = []
        for i, content in enumerate(contents):
            if i > 0 and i % 10 == 0:
                logger.info(f"Summarized {i}/{len(contents)} chunks")
            
            # Skip summarization for short content (e.g., less than 500 characters)
            if len(content) < 500:
                summaries.append(content)
                continue

            summary = await self.summarize(content)
            summaries.append(summary)
        return summaries

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instance
_summarizer: Summarizer | None = None


async def get_summarizer() -> Summarizer:
    """Get the global summarizer instance."""
    global _summarizer
    if _summarizer is None:
        _summarizer = Summarizer()
    return _summarizer
