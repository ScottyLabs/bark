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
    name="search_notion",
    description="Search Notion pages for information. Searches page titles and content in real-time using the Notion API. Use this to find ScottyLabs Notion documents, meeting notes, project pages, etc.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant Notion pages",
            },
        },
        "required": ["query"],
    },
)
def search_notion(query: str) -> str:
    """Search Notion pages using the native API."""
    engine = get_context_engine()
    return engine.search_notion_live(query)


@tool(
    name="search_drive",
    description="Search Google Drive files for information. Searches file names and content in real-time using the Drive API. Use this to find ScottyLabs documents, spreadsheets, presentations, etc.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant Drive files",
            },
        },
        "required": ["query"],
    },
)
def search_drive(query: str) -> str:
    """Search Google Drive files using the native API."""
    engine = get_context_engine()
    return engine.search_drive_live(query)


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

