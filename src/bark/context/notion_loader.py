"""Notion loader for fetching and parsing Notion workspace content."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


@dataclass
class NotionChunk:
    """A chunk of Notion content."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class NotionLoader:
    """Loads and parses content from a Notion workspace."""

    def __init__(
        self,
        api_key: str,
        chunk_size: int = 500,
    ) -> None:
        """Initialize the Notion loader.

        Args:
            api_key: Notion internal integration token
            chunk_size: Target size for content chunks (in words)
        """
        self.api_key = api_key
        self.chunk_size = chunk_size
        self._client: Client | None = None

    def _get_client(self) -> Client:
        """Get or create the Notion client."""
        if self._client is None:
            self._client = Client(auth=self.api_key)
        return self._client

    def load(self) -> list[NotionChunk]:
        """Fetch all accessible pages from Notion and parse them.

        Returns:
            List of Notion chunks
        """
        chunks: list[NotionChunk] = []

        try:
            client = self._get_client()

            # Search for all pages accessible to the integration
            logger.info("Fetching pages from Notion workspace")
            all_pages = self._fetch_all_pages(client)
            logger.info(f"Found {len(all_pages)} pages in Notion")

            for page in all_pages:
                page_chunks = self._parse_page(client, page)
                chunks.extend(page_chunks)

            logger.info(f"Loaded {len(chunks)} chunks from Notion")

        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load Notion content: {e}")
            raise

        return chunks

    def _fetch_all_pages(self, client: Client) -> list[dict[str, Any]]:
        """Fetch all pages accessible to the integration.

        Args:
            client: Notion client

        Returns:
            List of page objects
        """
        pages: list[dict[str, Any]] = []
        start_cursor = None

        while True:
            response = client.search(
                filter={"property": "object", "value": "page"},
                start_cursor=start_cursor,
                page_size=100,
            )

            pages.extend(response.get("results", []))

            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

        return pages

    def _parse_page(self, client: Client, page: dict[str, Any]) -> list[NotionChunk]:
        """Parse a Notion page into chunks.

        Args:
            client: Notion client
            page: Page object from Notion API

        Returns:
            List of chunks from this page
        """
        chunks: list[NotionChunk] = []
        page_id = page["id"]

        # Get page title
        page_title = self._get_page_title(page)
        page_url = page.get("url", "")

        # Fetch all blocks from the page
        try:
            blocks = self._fetch_all_blocks(client, page_id)
        except APIResponseError as e:
            logger.warning(f"Could not fetch blocks for page {page_title}: {e}")
            return chunks

        # Convert blocks to text
        content = self._blocks_to_text(blocks)

        if not content.strip():
            return chunks

        # Split into chunks
        text_chunks = self._split_into_chunks(content)

        for i, chunk_text in enumerate(text_chunks):
            chunk_id = self._generate_chunk_id(page_id, i)
            chunks.append(
                NotionChunk(
                    id=chunk_id,
                    content=chunk_text,
                    metadata={
                        "page": page_title,
                        "source": f"notion/{page_id}",
                        "url": page_url,
                        "source_type": "notion",
                    },
                )
            )

        return chunks

    def _get_page_title(self, page: dict[str, Any]) -> str:
        """Extract the page title from a page object.

        Args:
            page: Page object from Notion API

        Returns:
            Page title string
        """
        properties = page.get("properties", {})

        # Try common title property names
        for prop_name in ["title", "Title", "Name", "name"]:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop.get("type") == "title":
                    title_content = prop.get("title", [])
                    if title_content:
                        return "".join(t.get("plain_text", "") for t in title_content)

        # Fallback: check all properties for a title type
        for prop in properties.values():
            if prop.get("type") == "title":
                title_content = prop.get("title", [])
                if title_content:
                    return "".join(t.get("plain_text", "") for t in title_content)

        return "Untitled"

    def _fetch_all_blocks(
        self, client: Client, block_id: str
    ) -> list[dict[str, Any]]:
        """Recursively fetch all blocks from a page or block.

        Args:
            client: Notion client
            block_id: ID of the page or block

        Returns:
            List of block objects
        """
        blocks: list[dict[str, Any]] = []
        start_cursor = None

        while True:
            response = client.blocks.children.list(
                block_id=block_id,
                start_cursor=start_cursor,
                page_size=100,
            )

            for block in response.get("results", []):
                blocks.append(block)

                # Recursively fetch children if the block has them
                if block.get("has_children"):
                    child_blocks = self._fetch_all_blocks(client, block["id"])
                    blocks.extend(child_blocks)

            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

        return blocks

    def _blocks_to_text(self, blocks: list[dict[str, Any]]) -> str:
        """Convert Notion blocks to plain text.

        Args:
            blocks: List of block objects

        Returns:
            Plain text content
        """
        text_parts: list[str] = []

        for block in blocks:
            block_type = block.get("type", "")
            block_content = block.get(block_type, {})

            text = self._extract_text_from_block(block_type, block_content)
            if text:
                text_parts.append(text)

        return "\n".join(text_parts)

    def _extract_text_from_block(
        self, block_type: str, block_content: dict[str, Any]
    ) -> str:
        """Extract text from a single block.

        Args:
            block_type: Type of the block
            block_content: Content of the block

        Returns:
            Plain text from the block
        """
        # Handle rich text blocks
        rich_text_types = [
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "toggle",
            "quote",
            "callout",
        ]

        if block_type in rich_text_types:
            rich_text = block_content.get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text)

            # Add heading markers
            if block_type == "heading_1":
                text = f"# {text}"
            elif block_type == "heading_2":
                text = f"## {text}"
            elif block_type == "heading_3":
                text = f"### {text}"
            elif block_type == "bulleted_list_item":
                text = f"• {text}"
            elif block_type == "numbered_list_item":
                text = f"- {text}"
            elif block_type == "quote":
                text = f"> {text}"

            return text

        # Handle code blocks
        if block_type == "code":
            rich_text = block_content.get("rich_text", [])
            code = "".join(rt.get("plain_text", "") for rt in rich_text)
            language = block_content.get("language", "")
            return f"```{language}\n{code}\n```"

        # Handle to-do items
        if block_type == "to_do":
            rich_text = block_content.get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text)
            checked = block_content.get("checked", False)
            checkbox = "[x]" if checked else "[ ]"
            return f"{checkbox} {text}"

        # Handle dividers
        if block_type == "divider":
            return "---"

        # Handle table of contents (skip, it's meta)
        if block_type == "table_of_contents":
            return ""

        # Handle child pages (just note the reference)
        if block_type == "child_page":
            title = block_content.get("title", "Untitled")
            return f"[Child page: {title}]"

        # Handle child databases (just note the reference)
        if block_type == "child_database":
            title = block_content.get("title", "Untitled")
            return f"[Child database: {title}]"

        return ""

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks of approximately chunk_size words.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        words = text.split()

        if len(words) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        current_chunk: list[str] = []

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _generate_chunk_id(self, page_id: str, index: int) -> str:
        """Generate a unique ID for a chunk.

        Args:
            page_id: Notion page ID
            index: Chunk index within page

        Returns:
            Unique chunk ID
        """
        raw_id = f"notion:{page_id}:{index}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]
