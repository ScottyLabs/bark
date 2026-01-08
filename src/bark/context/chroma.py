"""ChromaDB client wrapper for vector storage."""

import logging
from dataclasses import dataclass, field
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document to store in the vector database."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    """A search result from the vector database."""

    id: str
    content: str
    metadata: dict[str, Any]
    distance: float


class ChromaClient:
    """Client for interacting with ChromaDB."""

    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        """Initialize the ChromaDB client.

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
        """
        self.host = host
        self.port = port
        self._client: chromadb.HttpClient | None = None
        self._collection_name = "scottylabs_wiki"

    def connect(self) -> None:
        """Connect to ChromaDB server."""
        try:
            self._client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Test connection
            self._client.heartbeat()
            logger.warning(f"Connected to ChromaDB at {self.host}:{self.port}.  There are {self.get_collection_count()} documents in the collection.")
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB at {self.host}:{self.port}: {e}. Using in-memory client.")
            self._client = chromadb.Client(
                settings=ChromaSettings(anonymized_telemetry=False),
            )

    def _get_or_create_collection(self) -> chromadb.Collection:
        """Get or create the wiki collection."""
        if not self._client:
            self.connect()
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"description": "ScottyLabs wiki content"},
        )

    def add_documents(self, documents: list[Document]) -> None:
        """Add documents to the collection.

        Args:
            documents: List of documents to add
        """
        if not documents:
            return

        collection = self._get_or_create_collection()

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        embeddings = [doc.embedding for doc in documents if doc.embedding]

        if embeddings and len(embeddings) == len(documents):
            collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
            )

        logger.info(f"Added {len(documents)} documents to collection")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
    ) -> list[SearchResult]:
        """Query the collection for similar documents.

        Args:
            query_embedding: The query embedding vector
            n_results: Number of results to return

        Returns:
            List of search results
        """
        collection = self._get_or_create_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                search_results.append(
                    SearchResult(
                        id=doc_id,
                        content=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        distance=results["distances"][0][i] if results["distances"] else 0.0,
                    )
                )

        return search_results

    def get_stored_notion_metadata(self) -> dict[str, str]:
        """Get stored metadata for all Notion pages in ChromaDB.

        Returns:
            Dictionary mapping page ID to last_edited_time
        """
        try:
            collection = self._get_or_create_collection()
            # Fetch all documents with source_type="notion"
            # Since we can't easily get "all" without a limit, we'll use a large limit
            # or iterate if needed. For now, we assume a reasonable limit.
            results = collection.get(
                where={"source_type": "notion"},
                include=["metadatas"],
            )

            metadata_map = {}
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    source = meta.get("source", "")
                    last_edited = meta.get("last_edited_time", "")
                    if source.startswith("notion/") and last_edited:
                        page_id = source.replace("notion/", "")
                        metadata_map[page_id] = last_edited
            
            return metadata_map
        except Exception as e:
            logger.error(f"Failed to fetch stored metadata: {e}")
            return {}

    def delete_notion_pages(self, page_ids: list[str]) -> None:
        """Delete all chunks associated with specific Notion pages.

        Args:
            page_ids: List of Notion page IDs
        """
        if not page_ids:
            return

        try:
            collection = self._get_or_create_collection()
            
            # Construct where clause for multiple pages
            # source in ["notion/id1", "notion/id2", ...]
            sources = [f"notion/{page_id}" for page_id in page_ids]
            
            collection.delete(
                where={"source": {"$in": sources}}
            )
            logger.info(f"Deleted chunks for {len(page_ids)} Notion pages")
        except Exception as e:
            logger.error(f"Failed to delete Notion pages: {e}")

    def get_stored_wiki_metadata(self) -> dict[str, str]:
        """Get stored metadata for all GitHub wiki pages in ChromaDB.

        Returns:
            Dictionary mapping relative file path to commit hash
        """
        try:
            collection = self._get_or_create_collection()
            results = collection.get(
                where={"source_type": "wiki"},
                include=["metadatas"],
            )

            metadata_map = {}
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    source = meta.get("source", "")
                    commit = meta.get("commit_hash", "")
                    # source is like "wiki/Home.md"
                    if source.startswith("wiki/") and commit:
                        path = source.replace("wiki/", "")
                        metadata_map[path] = commit
            
            return metadata_map
        except Exception as e:
            logger.error(f"Failed to fetch stored wiki metadata: {e}")
            return {}

    def delete_wiki_pages(self, paths: list[str]) -> None:
        """Delete all chunks associated with specific wiki pages.

        Args:
            paths: List of relative file paths
        """
        if not paths:
            return

        try:
            collection = self._get_or_create_collection()
            
            # source in ["wiki/path1", "wiki/path2", ...]
            sources = [f"wiki/{path}" for path in paths]
            
            collection.delete(
                where={"source": {"$in": sources}}
            )
            logger.info(f"Deleted chunks for {len(paths)} wiki pages")
        except Exception as e:
            logger.error(f"Failed to delete wiki pages: {e}")

    def delete_collection(self) -> None:
        """Delete the wiki collection."""
        if not self._client:
            self.connect()
        try:
            self._client.delete_collection(self._collection_name)
            logger.info(f"Deleted collection: {self._collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")

    def get_stored_drive_metadata(self) -> dict[str, str]:
        """Get stored metadata for all Google Drive files in ChromaDB.

        Returns:
            Dictionary mapping file ID to last_edited_time
        """
        try:
            collection = self._get_or_create_collection()
            results = collection.get(
                where={"source_type": "drive"},
                include=["metadatas"],
            )

            metadata_map = {}
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    source = meta.get("source", "")
                    last_edited = meta.get("last_edited_time", "")
                    # source is like "drive/{id}"
                    if source.startswith("drive/") and last_edited:
                        file_id = source.replace("drive/", "")
                        metadata_map[file_id] = last_edited
            
            return metadata_map
        except Exception as e:
            logger.error(f"Failed to fetch stored Drive metadata: {e}")
            return {}

    def delete_drive_files(self, file_ids: list[str]) -> None:
        """Delete all chunks associated with specific Drive files.

        Args:
            file_ids: List of Drive file IDs
        """
        if not file_ids:
            return

        try:
            collection = self._get_or_create_collection()
            
            # source in ["drive/id1", "drive/id2", ...]
            sources = [f"drive/{file_id}" for file_id in file_ids]
            
            collection.delete(
                where={"source": {"$in": sources}}
            )
            logger.info(f"Deleted chunks for {len(file_ids)} Drive files")
        except Exception as e:
            logger.error(f"Failed to delete Drive files: {e}")

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        try:
            collection = self._get_or_create_collection()
            return collection.count()
        except Exception:
            return 0
