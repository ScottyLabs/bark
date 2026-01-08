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

    def delete_collection(self) -> None:
        """Delete the wiki collection."""
        if not self._client:
            self.connect()
        try:
            self._client.delete_collection(self._collection_name)
            logger.info(f"Deleted collection: {self._collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        try:
            collection = self._get_or_create_collection()
            return collection.count()
        except Exception:
            return 0
