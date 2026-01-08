"""Memory tools for persistent storage across conversations."""

import json
import logging
from pathlib import Path

from bark.core.tools import tool

logger = logging.getLogger(__name__)

# Memory storage path - persists in container volume or locally
MEMORY_DIR = Path("/app/data/memory") if Path("/app").exists() else Path("./data/memory")


def _ensure_memory_dir() -> None:
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _get_memory_file() -> Path:
    """Get the memory file path."""
    _ensure_memory_dir()
    return MEMORY_DIR / "memory.json"


def _load_memory() -> dict[str, str]:
    """Load all memories from storage."""
    memory_file = _get_memory_file()
    if memory_file.exists():
        try:
            return json.loads(memory_file.read_text())
        except json.JSONDecodeError:
            logger.warning("Memory file corrupted, starting fresh")
            return {}
    return {}


def _save_memory(memory: dict[str, str]) -> None:
    """Save memories to storage."""
    memory_file = _get_memory_file()
    memory_file.write_text(json.dumps(memory, indent=2))


@tool(
    name="read_memory",
    description="Read a stored memory by key. Use this to recall information you've saved previously.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "The key/name of the memory to read. Use 'all' to list all memories.",
            },
        },
        "required": ["key"],
    },
)
async def read_memory(key: str) -> str:
    """Read a memory by key."""
    memory = _load_memory()

    if key == "all":
        if not memory:
            return "No memories stored yet."
        entries = [f"- **{k}**: {v}" for k, v in memory.items()]
        return f"Stored memories:\n" + "\n".join(entries)

    value = memory.get(key)
    if value:
        return f"Memory '{key}': {value}"
    return f"No memory found with key '{key}'."


@tool(
    name="write_memory",
    description="Save or update a memory. Use this to remember important information for future conversations, like user preferences, project details, or context.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "A short, descriptive key/name for the memory (e.g., 'user_timezone', 'project_status')",
            },
            "value": {
                "type": "string",
                "description": "The information to remember",
            },
        },
        "required": ["key", "value"],
    },
)
async def write_memory(key: str, value: str) -> str:
    """Write a memory."""
    memory = _load_memory()
    is_update = key in memory
    memory[key] = value
    _save_memory(memory)

    if is_update:
        return f"Updated memory '{key}'."
    return f"Saved new memory '{key}'."


@tool(
    name="delete_memory",
    description="Delete a stored memory by key.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "The key of the memory to delete",
            },
        },
        "required": ["key"],
    },
)
async def delete_memory(key: str) -> str:
    """Delete a memory."""
    memory = _load_memory()

    if key in memory:
        del memory[key]
        _save_memory(memory)
        return f"Deleted memory '{key}'."
    return f"No memory found with key '{key}'."


@tool(
    name="no_reply",
    description="Use this when you determine that no response is needed. For example, when a message wasn't directed at you, when someone is just chatting with others, or when your input wouldn't add value to the conversation.",
    parameters={
        "type": "object",
    },
)
async def no_reply() -> str:
    """Signal that no reply is needed."""
    return "__NO_REPLY__"
