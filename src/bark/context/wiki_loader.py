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

    def load(self, page_paths: list[str] | None = None) -> list[WikiChunk]:
        """Clone the wiki and parse markdown files.

        Args:
            page_paths: Optional list of specific file paths (relative to wiki root) to load.

        Returns:
            List of wiki chunks
        """
        chunks: list[WikiChunk] = []

        # Create temp directory for cloning
        temp_dir = tempfile.mkdtemp(prefix="bark_wiki_")
        try:
            logger.info(f"Cloning wiki from {self.repo_url}")
            git.Repo.clone_from(self.repo_url, temp_dir, depth=1)
            wiki_path = Path(temp_dir)

            if page_paths:
                logger.info(f"Processing {len(page_paths)} specific files")
                files_to_process = [wiki_path / path for path in page_paths]
            else:
                logger.info("Processing all markdown files")
                files_to_process = list(wiki_path.rglob("*.md"))

            # Find and parse files
            for md_file in files_to_process:
                if md_file.exists() and md_file.suffix == ".md":
                    # Get last commit hash for versioning (if available)
                    # For simplicty in this implementation, we rely on the caller to handle version tracking
                    # But we will add the commit hash/timestamp to metadata
                    file_chunks = self._parse_markdown_file(md_file, wiki_path)
                    chunks.extend(file_chunks)

            logger.info(f"Loaded {len(chunks)} chunks from wiki")

        except git.GitCommandError as e:
            logger.error(f"Failed to clone wiki: {e}")
            raise
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

        return chunks

    def fetch_page_metadata(self) -> dict[str, str]:
        """Fetch metadata for all wiki pages (path -> commit_hash).

        Returns:
            Dictionary mapping relative file path to last commit hash
        """
        temp_dir = tempfile.mkdtemp(prefix="bark_wiki_meta_")
        metadata = {}

        try:
            # We need full history or at least enough to get log, but depth 1 
            # is usually enough for the latest commit hash of the HEAD
            repo = git.Repo.clone_from(self.repo_url, temp_dir, depth=1)
            wiki_path = Path(temp_dir)
            
            # For each markdown file, get the blob hash or commit hash
            # A simple approximation for "version" is the blob hash (content hash) of the file
            # This is robust: if file content changes, blob hash changes.
            
            head_commit = repo.head.commit
            
            for md_file in wiki_path.rglob("*.md"):
                rel_path = md_file.relative_to(wiki_path)
                str_path = str(rel_path)
                
                try:
                    # Get blob hash for the file in the current HEAD
                    # This represents the exact content version
                    blob = head_commit.tree / str_path
                    metadata[str_path] = blob.hexsha
                except KeyError:
                    # File might not be in the tree if it's new/untracked? 
                    # But we just cloned so it should be there.
                    # Fallback to file hash
                    with open(md_file, "rb") as f:
                        file_hash = hashlib.sha1(f.read()).hexdigest()
                    metadata[str_path] = file_hash

        except Exception as e:
            logger.error(f"Failed to fetch wiki metadata: {e}")
            raise
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return metadata

    def _parse_markdown_file(self, file_path: Path, root_path: Path) -> list[WikiChunk]:
        """Parse a markdown file into chunks.

        Args:
            file_path: Path to the markdown file
            root_path: Root path of the wiki (to calculate relative path)

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
                            "source": f"wiki/{file_path.relative_to(root_path)}",
                            "source_type": "wiki",
                            # We can't easily get the blob hash here without re-calculating or passing it down
                            # But we'll rely on the engine to manage the "last_edited_time" equivalent
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
