"""Context tools for wiki search and refresh."""

from bark.context.engine import get_context_engine
from bark.core.tools import tool


@tool(
    name="refresh_context",
    description="Refresh the wiki context from GitHub. Use this when the wiki may have been updated or when search returns no results.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
async def refresh_context() -> str:
    """Refresh the wiki context by re-cloning and re-ingesting the wiki."""
    engine = get_context_engine()
    return await engine.refresh()


@tool(
    name="refresh_notion_context",
    description="Refresh the Notion context. Use this when Notion pages may have been updated or added.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
async def refresh_notion_context() -> str:
    """Refresh the Notion context by re-ingesting all pages."""
    engine = get_context_engine()
    return await engine.refresh_notion()


@tool(
    name="search_wiki",
    description="Search the ScottyLabs wiki for information about processes, projects, policies, or anything ScottyLabs-related. Returns relevant sections from the wiki.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant wiki content",
            },
        },
        "required": ["query"],
    },
)
async def search_wiki(query: str) -> str:
    """Search the wiki for relevant content."""
    engine = get_context_engine()
    return await engine.search_formatted(query)


# Import memory tools to register them
from bark.tools.memory_tools import (  # noqa: F401, E402
    read_memory,
    write_memory,
    delete_memory,
    no_reply,
)
