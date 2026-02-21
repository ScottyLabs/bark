"""Google Chat message handler for Bark.

Processes messages from Google Chat spaces through the ChatBot pipeline
and sends replies back to the originating space.  Maintains per-space
conversation state so follow-up messages preserve context.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from bark.core.chatbot import ChatBot, Conversation
from bark.core.config import Settings, get_settings
from bark.core.formatting import SLACK_FORMAT_INSTRUCTIONS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt addendum for Google Chat
# ---------------------------------------------------------------------------

GCHAT_SYSTEM_ADDENDUM = """You are communicating through Google Chat.

Use plain text formatting. Google Chat supports basic formatting:
- Bold: *text*
- Italic: _text_
- Strikethrough: ~text~
- Code: `code` or ```code block```
- Links are auto-detected from URLs.

Each message you receive is prefixed with "[From: username]" so you know who is speaking.
You can address users by name when appropriate.

Keep responses concise and helpful. You are responding to messages in a Google Chat space."""


# ---------------------------------------------------------------------------
# Data container for a parsed Google Chat message
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    """Parsed representation of a Google Chat message."""

    name: str  # Full message resource name (spaces/X/messages/Y)
    space_name: str  # Parent space resource name (spaces/X)
    sender_name: str  # Display name of the sender
    sender_email: str  # Email of the sender (if available)
    text: str  # Message text content
    create_time: str  # ISO timestamp
    thread_name: str  # Thread resource name for threaded replies


# ---------------------------------------------------------------------------
# GoogleChatHandler
# ---------------------------------------------------------------------------

@dataclass
class GoogleChatHandler:
    """Processes Google Chat messages and generates AI-powered replies.

    Manages per-space conversations so messages in the same space
    maintain context across exchanges.
    """

    settings: Settings = field(default_factory=get_settings)
    _chatbot: ChatBot | None = None
    _conversations: dict[str, Conversation] = field(default_factory=dict)
    _own_email: str | None = None

    async def __aenter__(self) -> "GoogleChatHandler":
        """Enter async context - initialise ChatBot."""
        self._chatbot = ChatBot(settings=self.settings)
        await self._chatbot.__aenter__()

        # Try to resolve our own identity to filter self-sent messages
        try:
            self._own_email = self._resolve_own_email()
            logger.info("Google Chat handler: resolved own email: %s", self._own_email)
        except Exception:
            logger.warning(
                "Could not resolve own email for Google Chat — "
                "will rely on display-name filtering only"
            )

        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context - clean up ChatBot."""
        if self._chatbot:
            await self._chatbot.__aexit__(*args)

    # ------------------------------------------------------------------
    # Google Chat API helpers
    # ------------------------------------------------------------------

    def _get_chat_service(self) -> Any:
        """Return the Google Chat API service object."""
        from bark.context.google_auth import get_google_auth
        return get_google_auth().chat

    def _resolve_own_email(self) -> str | None:
        """Try to determine the authenticated account's email.

        For service accounts this comes from the credentials info.
        For user OAuth it comes from the Gmail profile.
        """
        try:
            from bark.context.google_auth import get_google_auth
            auth = get_google_auth()
            creds = auth._get_credentials()
            # Service account credentials have a service_account_email attr
            if hasattr(creds, "service_account_email"):
                return creds.service_account_email
        except Exception:
            pass

        # Fallback: try Gmail profile
        try:
            from bark.context.google_auth import get_google_auth
            gmail = get_google_auth().gmail
            profile = gmail.users().getProfile(userId="me").execute()
            return profile.get("emailAddress")
        except Exception:
            pass

        return None

    def is_own_message(self, msg: ChatMessage) -> bool:
        """Check whether a message was sent by us (to prevent reply loops)."""
        if self._own_email and msg.sender_email:
            if msg.sender_email.lower() == self._own_email.lower():
                return True

        # Fallback: check display name for common bot patterns
        name_lower = msg.sender_name.lower()
        if name_lower in ("bark", "bark bot", "bark chatbot"):
            return True

        return False

    def fetch_messages(
        self, space_name: str, page_size: int = 50
    ) -> list[ChatMessage]:
        """Fetch recent messages from a Google Chat space.

        Runs synchronously (caller should wrap in asyncio.to_thread
        if needed). Returns messages in chronological order.
        """
        from bark.core.tools import _sync_tool_lock

        svc = self._get_chat_service()

        with _sync_tool_lock:
            result = svc.spaces().messages().list(
                parent=space_name, pageSize=page_size
            ).execute()

        messages: list[ChatMessage] = []
        for msg in result.get("messages", []):
            sender = msg.get("sender", {})
            text = msg.get("text", "")
            if not text:
                continue

            thread = msg.get("thread", {})
            messages.append(
                ChatMessage(
                    name=msg.get("name", ""),
                    space_name=space_name,
                    sender_name=sender.get("displayName", sender.get("name", "Unknown")),
                    sender_email=sender.get("name", ""),  # users/USER_ID or empty
                    text=text,
                    create_time=msg.get("createTime", ""),
                    thread_name=thread.get("name", ""),
                )
            )

        return messages

    def send_reply(self, space_name: str, text: str, thread_name: str = "") -> str | None:
        """Send a reply to a Google Chat space, optionally in a thread.

        Returns the sent message resource name on success, None on failure.
        """
        from bark.core.tools import _sync_tool_lock

        svc = self._get_chat_service()
        body: dict[str, Any] = {"text": text}
        if thread_name:
            body["thread"] = {"name": thread_name}

        try:
            with _sync_tool_lock:
                result = svc.spaces().messages().create(
                    parent=space_name,
                    body=body,
                    # messageReplyOption tells Chat to post in the thread
                    messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD" if thread_name else "MESSAGE_REPLY_OPTION_UNSPECIFIED",
                ).execute()
            return result.get("name")
        except Exception as e:
            logger.error("Failed to send Google Chat reply to %s: %s", space_name, e)
            return None

    # ------------------------------------------------------------------
    # ChatBot conversation management
    # ------------------------------------------------------------------

    def _get_or_create_conversation(self, space_name: str) -> Conversation:
        """Get or create a Conversation for a Chat space."""
        if space_name not in self._conversations:
            assert self._chatbot is not None
            self._conversations[space_name] = self._chatbot.create_conversation(
                system_prompt_addendum=GCHAT_SYSTEM_ADDENDUM,
            )
        return self._conversations[space_name]

    async def process_message(self, msg: ChatMessage) -> bool:
        """Generate an AI response and send it as a reply.

        Returns True if a reply was sent successfully.
        """
        if not self._chatbot:
            logger.error("GoogleChatHandler not initialised — call __aenter__ first")
            return False

        conversation = self._get_or_create_conversation(msg.space_name)

        # Build user message with sender identity
        user_message = f"[From: {msg.sender_name}] {msg.text}"

        try:
            response = await self._chatbot.chat(user_message, conversation)
        except Exception:
            logger.exception(
                "ChatBot error processing Google Chat message %s", msg.name
            )
            return False

        if not response or response.strip() == "__NO_REPLY__":
            logger.info("Bot chose not to reply to Chat message %s", msg.name)
            return False

        # Send reply (in the same thread if available)
        sent = await asyncio.to_thread(
            self.send_reply, msg.space_name, response, msg.thread_name
        )
        if sent:
            logger.info("Replied to Chat message %s → %s", msg.name, sent)
            return True

        return False

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def cleanup_old_conversations(self, max_spaces: int = 100) -> None:
        """Evict oldest conversations to cap memory usage."""
        if len(self._conversations) > max_spaces:
            keep = max_spaces // 2
            keys = list(self._conversations.keys())
            for key in keys[:-keep]:
                del self._conversations[key]
