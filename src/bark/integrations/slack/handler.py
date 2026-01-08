"""Slack event handlers."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient

from bark.core.chatbot import ChatBot, Conversation
from bark.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class SlackEventHandler:
    """Handles Slack events and routes them to the chatbot."""

    settings: Settings = field(default_factory=get_settings)
    _client: AsyncWebClient | None = None
    _chatbot: ChatBot | None = None
    _conversations: dict[str, Conversation] = field(default_factory=dict)
    _processed_events: set[str] = field(default_factory=set)

    async def __aenter__(self) -> "SlackEventHandler":
        """Enter async context."""
        self._client = AsyncWebClient(token=self.settings.slack_bot_token)
        self._chatbot = ChatBot(settings=self.settings)
        await self._chatbot.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._chatbot:
            await self._chatbot.__aexit__(*args)

    def _get_conversation_key(self, channel: str, thread_ts: str | None) -> str:
        """Get a unique key for a conversation thread."""
        if thread_ts:
            return f"{channel}:{thread_ts}"
        return channel

    def _get_or_create_conversation(
        self, channel: str, thread_ts: str | None
    ) -> Conversation:
        """Get or create a conversation for a channel/thread."""
        key = self._get_conversation_key(channel, thread_ts)

        if key not in self._conversations:
            self._conversations[key] = self._chatbot.create_conversation()

        return self._conversations[key]

    async def handle_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a Slack event.

        Args:
            event: The event payload from Slack

        Returns:
            Response to send back to Slack (if any)
        """
        event_type = event.get("type")

        if event_type == "url_verification":
            # Respond to Slack's URL verification challenge
            return {"challenge": event.get("challenge")}

        if event_type == "event_callback":
            inner_event = event.get("event", {})
            await self._handle_inner_event(inner_event, event.get("event_id"))

        return None

    async def _handle_inner_event(
        self, event: dict[str, Any], event_id: str | None
    ) -> None:
        """Handle the inner event from an event_callback."""
        # Deduplicate events
        if event_id and event_id in self._processed_events:
            logger.debug(f"Skipping duplicate event: {event_id}")
            return
        if event_id:
            self._processed_events.add(event_id)
            # Clean up old events (keep last 1000)
            if len(self._processed_events) > 1000:
                self._processed_events = set(list(self._processed_events)[-500:])

        event_type = event.get("type")

        if event_type == "app_mention":
            await self._handle_mention(event)
        elif event_type == "message":
            await self._handle_message(event)

    async def _handle_mention(self, event: dict[str, Any]) -> None:
        """Handle an app mention event."""
        # Get message details
        channel = event.get("channel", "")
        user = event.get("user", "")
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        ts = event.get("ts", "")

        # Remove the bot mention from the text
        # Mentions look like <@U123456>
        import re

        text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

        if not text:
            text = "Hello!"

        logger.info(f"Handling mention from {user} in {channel}: {text}")

        # Get or create conversation for this thread
        conversation = self._get_or_create_conversation(channel, thread_ts)

        # Process in background to respond quickly to Slack
        asyncio.create_task(
            self._process_and_respond(text, conversation, channel, thread_ts or ts)
        )

    async def _handle_message(self, event: dict[str, Any]) -> None:
        """Handle a direct message event."""
        # Ignore bot messages to prevent loops
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return

        # Only handle DMs (channel type 'im')
        channel_type = event.get("channel_type")
        if channel_type != "im":
            return

        channel = event.get("channel", "")
        user = event.get("user", "")
        text = event.get("text", "")
        thread_ts = event.get("thread_ts")
        ts = event.get("ts", "")

        if not text:
            return

        logger.info(f"Handling DM from {user}: {text}")

        # Get or create conversation for this DM
        conversation = self._get_or_create_conversation(channel, thread_ts)

        # Process in background
        asyncio.create_task(
            self._process_and_respond(text, conversation, channel, thread_ts or ts)
        )

    async def _process_and_respond(
        self,
        text: str,
        conversation: Conversation,
        channel: str,
        thread_ts: str,
    ) -> None:
        """Process a message and send a response."""
        if not self._chatbot or not self._client:
            logger.error("Handler not properly initialized")
            return

        try:
            # Get response from chatbot
            response = await self._chatbot.chat(text, conversation)

            # Send response to Slack
            await self._client.chat_postMessage(
                channel=channel,
                text=response,
                thread_ts=thread_ts,
            )

        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            try:
                await self._client.chat_postMessage(
                    channel=channel,
                    text="Sorry, I encountered an error processing your message. Please try again.",
                    thread_ts=thread_ts,
                )
            except Exception:
                logger.exception("Failed to send error message")
