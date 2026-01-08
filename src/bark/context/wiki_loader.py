"""Wiki loader for cloning and parsing GitHub wiki content."""

import hashlib
import logging
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import git

logger = logging.getLogger(__name__)


@dataclass
class WikiChunk:
    """A chunk of wiki content."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class WikiLoader:
    """Loads and parses content from a GitHub wiki."""

    def __init__(
        self,
        repo_url: str = "https://github.com/ScottyLabs/wiki.wiki.git",
        chunk_size: int = 500,
    ) -> None:
        """Initialize the wiki loader.

        Args:
            repo_url: URL of the wiki git repository
            chunk_size: Target size for content chunks (in words)
        """
        self.repo_url = repo_url
        self.chunk_size = chunk_size

    def load(self) -> list[WikiChunk]:
        """Clone the wiki and parse all markdown files.

        Returns:
            List of wiki chunks
        """
        chunks: list[WikiChunk] = []

        # Create temp directory for cloning
        temp_dir = tempfile.mkdtemp(prefix="bark_wiki_")
        try:
            logger.info(f"Cloning wiki from {self.repo_url}")
            git.Repo.clone_from(self.repo_url, temp_dir, depth=1)

            # Find and parse all markdown files
            wiki_path = Path(temp_dir)
            for md_file in wiki_path.glob("*.md"):
                file_chunks = self._parse_markdown_file(md_file)
                chunks.extend(file_chunks)

            logger.info(f"Loaded {len(chunks)} chunks from wiki")

        except git.GitCommandError as e:
            logger.error(f"Failed to clone wiki: {e}")
            raise
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

        return chunks

    def _parse_markdown_file(self, file_path: Path) -> list[WikiChunk]:
        """Parse a markdown file into chunks.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of chunks from this file
        """
        chunks: list[WikiChunk] = []
        page_name = file_path.stem.replace("-", " ").replace("_", " ")

        content = file_path.read_text(encoding="utf-8")

        # Split by headers
        sections = self._split_by_headers(content)

        for section in sections:
            heading = section.get("heading", "")
            text = section.get("text", "").strip()

            if not text:
                continue

            # Split large sections into smaller chunks
            section_chunks = self._split_into_chunks(text)

            for i, chunk_text in enumerate(section_chunks):
                chunk_id = self._generate_chunk_id(page_name, heading, i)
                chunks.append(
                    WikiChunk(
                        id=chunk_id,
                        content=chunk_text,
                        metadata={
                            "page": page_name,
                            "heading": heading,
                            "source": f"wiki/{file_path.name}",
                        },
                    )
                )

        return chunks

    def _split_by_headers(self, content: str) -> list[dict[str, str]]:
        """Split content by markdown headers.

        Args:
            content: Markdown content

        Returns:
            List of sections with heading and text
        """
        sections: list[dict[str, str]] = []

        # Match headers (# ## ### etc)
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(header_pattern.finditer(content))

        if not matches:
            # No headers, treat entire content as one section
            return [{"heading": "", "text": content}]

        # Add content before first header
        if matches[0].start() > 0:
            sections.append({"heading": "", "text": content[: matches[0].start()]})

        # Process each header section
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            text = content[start:end].strip()

            sections.append({"heading": heading, "text": text})

        return sections

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

    def _generate_chunk_id(self, page: str, heading: str, index: int) -> str:
        """Generate a unique ID for a chunk.

        Args:
            page: Page name
            heading: Section heading
            index: Chunk index within section

        Returns:
            Unique chunk ID
        """
        raw_id = f"{page}:{heading}:{index}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]
