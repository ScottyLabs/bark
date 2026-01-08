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
Keep responses clear and to the point. Use the search_wiki tool to find information from the ScottyLabs wiki when answering questions about ScottyLabs processes, projects, or policies."""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
