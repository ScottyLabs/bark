"""Background worker that periodically polls Google Chat spaces for new messages.

Runs as an asyncio task inside the FastAPI lifespan, checking configured
spaces for new messages at a regular interval and processing them through
the ChatBot pipeline.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from bark.core.config import Settings, get_settings
from bark.interfaces.gchat.handler import GoogleChatHandler

logger = logging.getLogger(__name__)

# Maximum number of consecutive poll errors before pausing with back-off
_MAX_CONSECUTIVE_ERRORS = 5
_BACKOFF_SECONDS = 300  # 5-minute pause after repeated failures


class GoogleChatWorker:
    """Periodically polls Google Chat spaces for new messages and responds.

    Usage::

        worker = GoogleChatWorker(settings=settings)
        await worker.start()   # launches background task
        ...
        await worker.stop()    # graceful shutdown
    """

    def __init__(
        self,
        settings: Settings | None = None,
        poll_interval: int | None = None,
        space_ids: list[str] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._poll_interval = (
            poll_interval
            if poll_interval is not None
            else self._settings.gchat_poll_interval
        )
        # Space IDs to poll — from constructor or settings
        raw = space_ids or self._parse_space_ids(self._settings.gchat_space_ids)
        # Normalise: ensure each ID starts with "spaces/"
        self._space_ids: list[str] = [
            sid if sid.startswith("spaces/") else f"spaces/{sid}"
            for sid in raw
        ]

        self._handler: GoogleChatHandler | None = None
        self._task: asyncio.Task[Any] | None = None
        self._running = False
        self._consecutive_errors = 0

        # Track the latest message timestamp we've seen per space so we only
        # process genuinely new messages.  Maps space_name → ISO timestamp str.
        self._last_seen: dict[str, str] = {}

    @staticmethod
    def _parse_space_ids(raw: str) -> list[str]:
        """Parse a comma-separated list of space IDs from config."""
        if not raw:
            return []
        return [s.strip() for s in raw.split(",") if s.strip()]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Initialise the handler and launch the polling loop."""
        if self._running:
            logger.warning("GoogleChatWorker is already running")
            return

        if not self._space_ids:
            logger.warning(
                "GoogleChatWorker: no space IDs configured — "
                "set GCHAT_SPACE_IDS to enable Google Chat polling"
            )
            return

        self._handler = GoogleChatHandler(settings=self._settings)
        await self._handler.__aenter__()
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name="gchat-worker")
        logger.info(
            "GoogleChatWorker started — polling %d space(s) every %ds: %s",
            len(self._space_ids),
            self._poll_interval,
            ", ".join(self._space_ids),
        )

    async def stop(self) -> None:
        """Stop the polling loop and clean up resources."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._handler:
            await self._handler.__aexit__(None, None, None)
            self._handler = None

        logger.info("GoogleChatWorker stopped")

    # ------------------------------------------------------------------
    # Internal polling loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Main loop: fetch → process → sleep → repeat."""
        # Brief startup delay so other services can initialise first
        await asyncio.sleep(5)

        # Seed _last_seen with the current latest message per space so we
        # don't re-process messages that existed before the worker started.
        await self._seed_last_seen()

        while self._running:
            try:
                await self._poll_once()
                self._consecutive_errors = 0
            except asyncio.CancelledError:
                raise
            except Exception:
                self._consecutive_errors += 1
                logger.exception(
                    "Error during Google Chat poll cycle (%d/%d consecutive)",
                    self._consecutive_errors,
                    _MAX_CONSECUTIVE_ERRORS,
                )

                if self._consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    logger.warning(
                        "Too many consecutive Google Chat poll errors — "
                        "backing off for %ds",
                        _BACKOFF_SECONDS,
                    )
                    try:
                        await asyncio.sleep(_BACKOFF_SECONDS)
                    except asyncio.CancelledError:
                        raise
                    self._consecutive_errors = 0
                    continue

            try:
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                raise

    async def _seed_last_seen(self) -> None:
        """Fetch the latest message per space to initialise the watermark.

        This prevents the worker from replying to old messages on first boot.
        """
        assert self._handler is not None

        for space in self._space_ids:
            try:
                messages = await asyncio.to_thread(
                    self._handler.fetch_messages, space, 1
                )
                if messages:
                    self._last_seen[space] = messages[-1].create_time
                    logger.debug(
                        "Seeded last_seen for %s: %s",
                        space,
                        self._last_seen[space],
                    )
                else:
                    # No messages yet — mark as "now" so future messages are new
                    self._last_seen[space] = datetime.now(timezone.utc).isoformat()
            except Exception:
                logger.warning(
                    "Failed to seed last_seen for space %s — "
                    "will process all recent messages on first poll",
                    space,
                    exc_info=True,
                )
                self._last_seen[space] = datetime.now(timezone.utc).isoformat()

    async def _poll_once(self) -> None:
        """Run a single poll-and-process cycle across all configured spaces."""
        assert self._handler is not None

        for space in self._space_ids:
            try:
                messages = await asyncio.to_thread(
                    self._handler.fetch_messages, space, 50
                )
            except Exception:
                logger.exception("Failed to fetch messages for space %s", space)
                continue

            if not messages:
                continue

            # Filter to only messages newer than our watermark
            watermark = self._last_seen.get(space, "")
            new_messages = [
                m for m in messages
                if m.create_time > watermark
            ] if watermark else messages

            if not new_messages:
                continue

            logger.info(
                "Found %d new message(s) in %s",
                len(new_messages),
                space,
            )

            for msg in new_messages:
                # Skip our own messages to prevent reply loops
                if self._handler.is_own_message(msg):
                    logger.debug("Skipping own message %s", msg.name)
                    continue

                logger.info(
                    "Processing Chat message from %s in %s: %s",
                    msg.sender_name,
                    space,
                    msg.text[:100],
                )

                # Ingest to Chroma for semantic memory
                self._ingest_to_chroma(msg)

                try:
                    await self._handler.process_message(msg)
                except Exception:
                    logger.exception(
                        "Error processing Chat message %s", msg.name
                    )

            # Update watermark to the latest message in this batch
            self._last_seen[space] = new_messages[-1].create_time

        # Periodic housekeeping
        if self._handler:
            self._handler.cleanup_old_conversations()

    def _ingest_to_chroma(self, msg: Any) -> None:
        """Push a Chat message to Chroma for semantic memory."""
        try:
            from bark.context.chroma import ChromaClient, Document
            from uuid import uuid4

            async def _do_ingest() -> None:
                client = ChromaClient(
                    host=self._settings.chroma_host,
                    port=self._settings.chroma_port,
                )
                try:
                    client.connect()
                except Exception:
                    pass

                doc = Document(
                    id=str(uuid4()),
                    content=msg.text,
                    metadata={
                        "source_type": "google_chat",
                        "sender": msg.sender_name,
                        "space": msg.space_name,
                        "timestamp": msg.create_time or datetime.now(timezone.utc).isoformat(),
                    },
                )
                client.add_documents([doc])

            asyncio.create_task(_do_ingest())
        except Exception as e:
            logger.warning("Failed to ingest Chat message to Chroma: %s", e)
