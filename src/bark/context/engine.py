"""Context engine orchestrating wiki loading, embedding, and search."""

import logging
from dataclasses import dataclass, field

from bark.context.chroma import ChromaClient, Document, SearchResult
from bark.context.embeddings import EmbeddingGenerator
from bark.context.summarizer import Summarizer
from bark.context.summarizer import Summarizer
from bark.context.notion_loader import NotionLoader
from bark.context.drive_loader import DriveLoader
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
    _loader: WikiLoader | None = None
    _notion_loader: NotionLoader | None = None
    _drive_loader: DriveLoader | None = None

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

    def _get_drive_loader(self) -> DriveLoader | None:
        """Get or create Drive loader if configured."""
        if self._drive_loader is None and (
            self.settings.google_drive_credentials_file 
            or self.settings.google_drive_credentials_json 
            or self.settings.google_drive_token_json
        ):
            # Parse comma-separated exclude folder IDs
            exclude_ids = [
                fid.strip() 
                for fid in self.settings.google_drive_exclude_folder_ids.split(",") 
                if fid.strip()
            ]
            self._drive_loader = DriveLoader(
                credentials_file=self.settings.google_drive_credentials_file,
                credentials_json=self.settings.google_drive_credentials_json,
                token_json=self.settings.google_drive_token_json,
                folder_id=self.settings.google_drive_folder_id,
                exclude_folder_ids=exclude_ids,
            )
        return self._drive_loader

    async def refresh(self) -> str:
        """Refresh the wiki context incrementally.

        Returns:
            Status message
        """
        try:
            chroma = self._get_chroma()
            embedder = self._get_embedder()
            loader = self._get_loader()

            # 1. Fetch metadata for all current wiki pages
            logger.info("Fetching wiki metadata...")
            current_metadata = loader.fetch_page_metadata()
            current_paths = set(current_metadata.keys())

            # 2. Get stored metadata from Chroma
            stored_metadata = chroma.get_stored_wiki_metadata()
            stored_paths = set(stored_metadata.keys())

            # 3. Determine changes
            new_pages = current_paths - stored_paths
            deleted_pages = stored_paths - current_paths
            
            # For pages in both, check if commit hash changed
            updated_pages = {
                path for path in (current_paths & stored_paths)
                if current_metadata[path] != stored_metadata[path]
            }

            pages_to_process = list(new_pages | updated_pages)
            pages_to_delete = list(deleted_pages | updated_pages)

            stats = {
                "new": len(new_pages),
                "updated": len(updated_pages),
                "deleted": len(deleted_pages),
                "unchanged": len(current_paths) - len(new_pages) - len(updated_pages)
            }
            logger.info(f"Incremental wiki refresh stats: {stats}")

            if not pages_to_process and not pages_to_delete:
                return "Wiki context is up to date."

            # 4. Process deletions
            if pages_to_delete:
                logger.info(f"Deleting chunks for {len(pages_to_delete)} wiki pages")
                chroma.delete_wiki_pages(pages_to_delete)

            # 5. Process new/updated pages
            if pages_to_process:
                logger.info(f"Processing {len(pages_to_process)} new/updated wiki pages")
                chunks = loader.load(page_paths=pages_to_process)
                
                if chunks:
                    # Update metadata with commit hashes
                    for chunk in chunks:
                        # source is like "wiki/path/to/file.md"
                        relative_path = chunk.metadata["source"].replace("wiki/", "")
                        if relative_path in current_metadata:
                            chunk.metadata["commit_hash"] = current_metadata[relative_path]

                    # Summarize
                    logger.info(f"Summarizing {len(chunks)} chunks")
                    original_texts = [chunk.content for chunk in chunks]
                    summarizer = self._get_summarizer()
                    summaries = await summarizer.summarize_batch(original_texts)

                    # Embed
                    logger.info(f"Generating embeddings for {len(summaries)} summaries")
                    embeddings = await embedder.embed_batch(summaries)

                    # Create documents
                    documents = [
                        Document(
                            id=chunk.id,
                            content=chunk.content,
                            metadata=chunk.metadata,
                            embedding=embedding,
                        )
                        for chunk, embedding in zip(chunks, embeddings)
                    ]

                    # Add to Chroma
                    chroma.add_documents(documents)

            return (
                f"Refreshed wiki context: "
                f"{stats['new']} new, {stats['updated']} updated, "
                f"{stats['deleted']} deleted, {stats['unchanged']} unchanged."
            )

        except Exception as e:
            logger.error(f"Failed to refresh context: {e}")
            return f"Failed to refresh wiki context: {str(e)}"

    async def refresh_notion(self) -> str:
        """Refresh the Notion context incrementally.

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

            # 1. Fetch metadata for all current pages from Notion
            logger.info("Fetching Notion page metadata...")
            current_metadata = notion_loader.fetch_page_metadata()
            current_page_ids = set(current_metadata.keys())

            # 2. Get stored metadata from Chroma
            stored_metadata = chroma.get_stored_notion_metadata()
            stored_page_ids = set(stored_metadata.keys())

            # 3. Determine changes
            new_pages = current_page_ids - stored_page_ids
            deleted_pages = stored_page_ids - current_page_ids
            
            # For pages in both, check if timestamp changed
            # Note: Notion timestamps are ISO 8601 strings, so string comparison works
            updated_pages = {
                pid for pid in (current_page_ids & stored_page_ids)
                if current_metadata[pid] > stored_metadata[pid]
            }

            pages_to_process = list(new_pages | updated_pages)
            pages_to_delete = list(deleted_pages | updated_pages)

            stats = {
                "new": len(new_pages),
                "updated": len(updated_pages),
                "deleted": len(deleted_pages),
                "unchanged": len(current_page_ids) - len(new_pages) - len(updated_pages)
            }
            logger.info(f"Incremental refresh stats: {stats}")

            if not pages_to_process and not pages_to_delete:
                return "Notion context is up to date."

            # 4. Process deletions (including outdated versions of updated pages)
            if pages_to_delete:
                logger.info(f"Deleting chunks for {len(pages_to_delete)} pages")
                chroma.delete_notion_pages(pages_to_delete)

            # 5. Process new/updated pages
            if pages_to_process:
                logger.info(f"Processing {len(pages_to_process)} new/updated pages")
                
                chunks = notion_loader.load(page_ids=pages_to_process)
                
                if chunks:
                    # Summarize chunks
                    logger.info(f"Summarizing {len(chunks)} chunks")
                    original_texts = [chunk.content for chunk in chunks]
                    summaries = await summarizer.summarize_batch(original_texts)

                    # Generate embeddings
                    logger.info(f"Generating embeddings for {len(summaries)} summaries")
                    embeddings = await embedder.embed_batch(summaries)

                    # Create documents
                    documents = [
                        Document(
                            id=chunk.id,
                            content=chunk.content,
                            metadata=chunk.metadata,
                            embedding=embedding,
                        )
                        for chunk, embedding in zip(chunks, embeddings)
                    ]

                    # Add to Chroma
                    chroma.add_documents(documents)

            return (
                f"Refreshed Notion context: "
                f"{stats['new']} new, {stats['updated']} updated, "
                f"{stats['deleted']} deleted, {stats['unchanged']} unchanged."
            )

        except Exception as e:
            logger.error(f"Failed to refresh Notion context: {e}")
            return f"Failed to refresh Notion context: {str(e)}"

    async def refresh_drive(self) -> str:
        """Refresh the Google Drive context incrementally.

        Returns:
            Status message
        """
        drive_loader = self._get_drive_loader()
        if drive_loader is None:
            return "Google Drive integration not configured. Check google_drive_credentials_file or GOOGLE_DRIVE_CREDENTIALS_JSON/TOKEN_JSON settings."

        try:
            chroma = self._get_chroma()
            embedder = self._get_embedder()
            summarizer = self._get_summarizer()

            # 1. Fetch metadata for all current files from Drive
            logger.info("Fetching Drive file metadata...")
            current_metadata = drive_loader.fetch_file_metadata()
            current_file_ids = set(current_metadata.keys())

            # 2. Get stored metadata from Chroma
            stored_metadata = chroma.get_stored_drive_metadata()
            stored_file_ids = set(stored_metadata.keys())

            # 3. Determine changes
            new_files = current_file_ids - stored_file_ids
            deleted_files = stored_file_ids - current_file_ids
            
            # For files in both, check if timestamp changed
            # Drive timestamps are ISO strings
            updated_files = {
                fid for fid in (current_file_ids & stored_file_ids)
                if current_metadata[fid] > stored_metadata[fid]
            }

            files_to_process = list(new_files | updated_files)
            files_to_delete = list(deleted_files | updated_files)

            stats = {
                "new": len(new_files),
                "updated": len(updated_files),
                "deleted": len(deleted_files),
                "unchanged": len(current_file_ids) - len(new_files) - len(updated_files)
            }
            logger.info(f"Incremental Drive refresh stats: {stats}")

            if not files_to_process and not files_to_delete:
                return "Google Drive context is up to date."

            # 4. Process deletions
            if files_to_delete:
                logger.info(f"Deleting chunks for {len(files_to_delete)} Drive files")
                chroma.delete_drive_files(files_to_delete)

            # 5. Process new/updated files
            if files_to_process:
                logger.info(f"Processing {len(files_to_process)} new/updated Drive files")
                chunks = drive_loader.load(file_ids=files_to_process)
                
                if chunks:
                    # Summarize chunks
                    logger.info(f"Summarizing {len(chunks)} chunks")
                    original_texts = [chunk.content for chunk in chunks]
                    summaries = await summarizer.summarize_batch(original_texts)

                    # Generate embeddings
                    logger.info(f"Generating embeddings for {len(summaries)} summaries")
                    embeddings = await embedder.embed_batch(summaries)

                    # Create documents
                    documents = [
                        Document(
                            id=chunk.id,
                            content=chunk.content,
                            metadata=chunk.metadata,
                            embedding=embedding,
                        )
                        for chunk, embedding in zip(chunks, embeddings)
                    ]

                    # Add to Chroma
                    chroma.add_documents(documents)

            return (
                f"Refreshed Google Drive context: "
                f"{stats['new']} new, {stats['updated']} updated, "
                f"{stats['deleted']} deleted, {stats['unchanged']} unchanged."
            )

        except Exception as e:
            logger.error(f"Failed to refresh Google Drive context: {e}")
            return f"Failed to refresh Google Drive context: {str(e)}"

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
