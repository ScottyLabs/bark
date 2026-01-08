"""Context engine orchestrating wiki loading, embedding, and search."""

import logging
from dataclasses import dataclass, field

from bark.context.chroma import ChromaClient, Document, SearchResult
from bark.context.embeddings import EmbeddingGenerator
from bark.context.summarizer import Summarizer
from bark.context.notion_loader import NotionLoader
from bark.context.wiki_loader import WikiLoader
from bark.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class ContextEngine:
    """Orchestrates the RAG pipeline for wiki context."""

    settings: Settings = field(default_factory=get_settings)
    _chroma: ChromaClient | None = None
    _embedder: EmbeddingGenerator | None = None
    _summarizer: Summarizer | None = None
    _loader: WikiLoader | None = None
    _notion_loader: NotionLoader | None = None

    def _get_chroma(self) -> ChromaClient:
        """Get or create ChromaDB client."""
        if self._chroma is None:
            self._chroma = ChromaClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
            )
        return self._chroma

    def _get_embedder(self) -> EmbeddingGenerator:
        """Get or create embedding generator."""
        if self._embedder is None:
            self._embedder = EmbeddingGenerator()
        return self._embedder

    def _get_summarizer(self) -> Summarizer:
        """Get or create summarizer."""
        if self._summarizer is None:
            self._summarizer = Summarizer()
        return self._summarizer

    def _get_loader(self) -> WikiLoader:
        """Get or create wiki loader."""
        if self._loader is None:
            self._loader = WikiLoader(repo_url=self.settings.wiki_repo_url)
        return self._loader

    def _get_notion_loader(self) -> NotionLoader | None:
        """Get or create Notion loader if configured."""
        if self._notion_loader is None and self.settings.notion_api_key:
            self._notion_loader = NotionLoader(api_key=self.settings.notion_api_key)
        return self._notion_loader

    async def refresh(self) -> str:
        """Refresh the wiki context by re-ingesting all content.

        Returns:
            Status message
        """
        try:
            chroma = self._get_chroma()
            embedder = self._get_embedder()
            loader = self._get_loader()

            # Clear existing collection
            chroma.delete_collection()

            # Load wiki content
            chunks = loader.load()

            if not chunks:
                return "No wiki content found to ingest."

            # Summarize chunks for embedding (cheaper than embedding full content)
            summarizer = self._get_summarizer()
            logger.info(f"Summarizing {len(chunks)} chunks for embedding")
            original_texts = [chunk.content for chunk in chunks]
            summaries = await summarizer.summarize_batch(original_texts)

            # Generate embeddings from summaries
            logger.info(f"Generating embeddings for {len(summaries)} summaries")
            embeddings = await embedder.embed_batch(summaries)

            # Create documents with embeddings
            documents = [
                Document(
                    id=chunk.id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]

            # Add to ChromaDB
            chroma.add_documents(documents)

            count = chroma.get_collection_count()
            return f"Successfully refreshed wiki context. Ingested {count} chunks from the ScottyLabs wiki."

        except Exception as e:
            logger.error(f"Failed to refresh context: {e}")
            return f"Failed to refresh wiki context: {str(e)}"

    async def refresh_notion(self) -> str:
        """Refresh the Notion context by re-ingesting all Notion pages.

        Returns:
            Status message
        """
        notion_loader = self._get_notion_loader()
        if notion_loader is None:
            return "Notion integration not configured. Set NOTION_API_KEY in your environment."

        try:
            chroma = self._get_chroma()
            embedder = self._get_embedder()
            summarizer = self._get_summarizer()

            # Load Notion content
            logger.info("Loading content from Notion workspace")
            chunks = notion_loader.load()

            if not chunks:
                return "No Notion content found to ingest."

            # Summarize chunks for embedding
            logger.info(f"Summarizing {len(chunks)} Notion chunks for embedding")
            original_texts = [chunk.content for chunk in chunks]
            summaries = await summarizer.summarize_batch(original_texts)

            # Generate embeddings from summaries
            logger.info(f"Generating embeddings for {len(summaries)} Notion summaries")
            embeddings = await embedder.embed_batch(summaries)

            # Create documents with embeddings
            documents = [
                Document(
                    id=chunk.id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]

            # Add to ChromaDB (same collection as wiki)
            chroma.add_documents(documents)

            return f"Successfully refreshed Notion context. Ingested {len(documents)} chunks from Notion workspace."

        except Exception as e:
            logger.error(f"Failed to refresh Notion context: {e}")
            return f"Failed to refresh Notion context: {str(e)}"

    async def search(self, query: str, k: int = 5) -> list[SearchResult]:
        """Search for relevant wiki content.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results
        """
        try:
            chroma = self._get_chroma()
            embedder = self._get_embedder()

            # Check if we have any documents
            if chroma.get_collection_count() == 0:
                logger.warning("No documents in collection. Run refresh first.")
                return []

            # Generate query embedding (now async)
            query_embedding = await embedder.embed(query)

            # Search
            results = chroma.query(query_embedding, n_results=k)
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def search_formatted(self, query: str, k: int = 5) -> str:
        """Search and return formatted results.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Formatted search results string
        """
        results = await self.search(query, k)

        if not results:
            return "No relevant wiki content found. The wiki may need to be refreshed using the refresh_context tool."

        output_parts = [f"Found {len(results)} relevant wiki sections:\n"]

        for i, result in enumerate(results, 1):
            page = result.metadata.get("page", "Unknown")
            heading = result.metadata.get("heading", "")
            source = result.metadata.get("source", "")

            header = f"**{page}**"
            if heading:
                header += f" > {heading}"

            output_parts.append(f"### {i}. {header}")
            output_parts.append(f"*Source: {source}*\n")
            output_parts.append(result.content)
            output_parts.append("")

        return "\n".join(output_parts)


# Global instance for tools
_engine: ContextEngine | None = None


def get_context_engine() -> ContextEngine:
    """Get the global context engine instance."""
    global _engine
    if _engine is None:
        _engine = ContextEngine()
    return _engine
