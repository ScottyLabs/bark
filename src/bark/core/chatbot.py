"""Main ChatBot class that coordinates conversations."""

from dataclasses import dataclass, field

from bark.core.config import Settings, get_settings
from bark.core.openrouter import Message, OpenRouterClient
from bark.core.tools import ToolRegistry, get_registry


@dataclass
class Conversation:
    """Manages a single conversation's state."""

    messages: list[Message] = field(default_factory=list)
    system_prompt: str = ""

    def __post_init__(self) -> None:
        """Initialize with system prompt if provided."""
        if self.system_prompt and not self.messages:
            self.messages.append(Message(role="system", content=self.system_prompt))

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self.messages.append(Message(role="assistant", content=content))

    def get_messages(self) -> list[Message]:
        """Get all messages in the conversation."""
        return self.messages.copy()


@dataclass
class ChatBot:
    """Main chatbot interface.

    Usage:
        async with ChatBot() as bot:
            response = await bot.chat("Hello!")
            print(response)
    """

    settings: Settings = field(default_factory=get_settings)
    registry: ToolRegistry = field(default_factory=get_registry)
    _client: OpenRouterClient | None = None

    async def __aenter__(self) -> "ChatBot":
        """Enter async context."""
        self._client = OpenRouterClient(
            settings=self.settings,
            registry=self.registry,
        )
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context."""
        if self._client:
            await self._client.__aexit__(*args)

    def create_conversation(
        self,
        system_prompt: str | None = None,
        system_prompt_addendum: str | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            system_prompt: Optional custom system prompt. Uses default if not provided.
            system_prompt_addendum: Optional addendum to append to the system prompt.
                Useful for integration-specific instructions (e.g., Slack formatting).
        """
        prompt = system_prompt or self.settings.system_prompt
        if system_prompt_addendum:
            prompt = f"{prompt}\n\n{system_prompt_addendum}"
        return Conversation(
            system_prompt=prompt,
        )

    async def chat(
        self,
        message: str,
        conversation: Conversation | None = None,
    ) -> str:
        """Send a message and get a response.

        Args:
            message: The user's message
            conversation: Optional conversation to continue. Creates new one if not provided.

        Returns:
            The assistant's response text
        """
        if not self._client:
            raise RuntimeError("ChatBot not initialized. Use 'async with' context.")

        # Create or use existing conversation
        if conversation is None:
            conversation = self.create_conversation()

        # Add user message
        conversation.add_user_message(message)

        # Get response from OpenRouter
        response = await self._client.chat(conversation.get_messages())

        # Add response to conversation
        content = response.content or ""
        conversation.add_assistant_message(content)

        return content

    async def simple_chat(self, message: str) -> str:
        """Send a single message without conversation history.

        Useful for one-off questions.
        """
        if not self._client:
            raise RuntimeError("ChatBot not initialized. Use 'async with' context.")

        messages = [
            Message(role="system", content=self.settings.system_prompt),
            Message(role="user", content=message),
        ]

        response = await self._client.chat(messages)
        return response.content or ""
