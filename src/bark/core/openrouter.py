"""OpenRouter API client for chat completions with tool support."""

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

from bark.core.config import Settings, get_settings
from bark.core.tools import ToolRegistry, get_registry


@dataclass
class Message:
    """A chat message."""

    role: str  # "system", "user", "assistant", or "tool"
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API format."""
        msg: dict[str, Any] = {"role": self.role}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls is not None:
            msg["tool_calls"] = self.tool_calls

        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id

        if self.name is not None:
            msg["name"] = self.name

        return msg


@dataclass
class OpenRouterClient:
    """Async client for OpenRouter API."""

    settings: Settings = field(default_factory=get_settings)
    registry: ToolRegistry = field(default_factory=get_registry)
    _client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OpenRouterClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://scottylabs.org",
                "X-Title": "Bark ChatBot",
            },
            timeout=60.0,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
    ) -> Message:
        """Send a chat completion request and handle tool calls.

        This method will automatically execute tool calls and continue
        the conversation until a final response is received.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        model = model or self.settings.openrouter_model
        conversation = list(messages)  # Copy to avoid mutating input

        while True:
            # Build request payload
            payload: dict[str, Any] = {
                "model": model,
                "messages": [m.to_dict() for m in conversation],
            }

            # Add tools if available
            tools = self.registry.to_openai_schema()
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            # Make request
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            # Parse response
            choice = data["choices"][0]
            message = choice["message"]

            # Check if we're done
            if choice.get("finish_reason") == "stop" or not message.get("tool_calls"):
                return Message(
                    role="assistant",
                    content=message.get("content", ""),
                )

            # Handle tool calls
            assistant_msg = Message(
                role="assistant",
                content=message.get("content"),
                tool_calls=message["tool_calls"],
            )
            conversation.append(assistant_msg)

            # Execute each tool call
            for tool_call in message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                # Handle empty/missing arguments (e.g., refresh_context with no params)
                args_str = tool_call["function"].get("arguments", "{}") or "{}"
                tool_args = json.loads(args_str)

                tool = self.registry.get(tool_name)
                if tool:
                    try:
                        result = await tool.execute(**tool_args)
                    except Exception as e:
                        result = f"Error executing tool: {e}"
                else:
                    result = f"Unknown tool: {tool_name}"

                # Add tool result to conversation
                tool_msg = Message(
                    role="tool",
                    content=result,
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
                conversation.append(tool_msg)

            # Continue loop to get final response
