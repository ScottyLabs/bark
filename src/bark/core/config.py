"""Configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Slack Configuration
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Context Engine Configuration
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    wiki_repo_url: str = "https://github.com/ScottyLabs/wiki.wiki.git"
    embedding_model: str = "openai/text-embedding-3-small"

    # Bot Configuration
    system_prompt: str = """You are Bark, a helpful assistant for ScottyLabs (scottylabs.org). 
You are friendly, concise, and helpful. You can use tools when available to help answer questions.

**Tools available:**
- search_wiki: Search the ScottyLabs wiki for processes, projects, and policies
- refresh_context: Refresh wiki content from GitHub
- read_memory/write_memory/delete_memory: Persistent memory across conversations
- no_reply: Use when your response isn't needed (e.g., message not directed at you, casual chat between others)

**Guidelines:**
- Use search_wiki for ScottyLabs-specific questions
- Use memory tools to remember important context, user preferences, or ongoing discussions
- Use no_reply when you're not being addressed or your input wouldn't add value
- Keep responses clear and concise. Use Slack-compatible markdown."""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
