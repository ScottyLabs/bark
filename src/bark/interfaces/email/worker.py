"""Background worker that periodically polls Gmail for new emails.

Runs as an asyncio task inside the FastAPI lifespan, checking for
messages labelled ``bark-unread`` sent to the configured target address
at a regular interval.
"""

import asyncio
import logging
from typing import Any

from bark.core.config import Settings, get_settings
from bark.interfaces.email.handler import EmailHandler

logger = logging.getLogger(__name__)

# Maximum number of consecutive poll errors before pausing with back-off
_MAX_CONSECUTIVE_ERRORS = 5
_BACKOFF_SECONDS = 300  # 5-minute pause after repeated failures


class EmailWorker:
    """Periodically polls Gmail for ``bark-unread`` emails and processes them.

    Usage::

        worker = EmailWorker(settings=settings)
        await worker.start()   # launches background task
        ...
        await worker.stop()    # graceful shutdown
    """

    def __init__(
        self,
        settings: Settings | None = None,
        poll_interval: int | None = None,
        target_address: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._poll_interval = (
            poll_interval
            if poll_interval is not None
            else self._settings.email_poll_interval
        )
        self._target_address = target_address or self._settings.email_target_address
        self._handler: EmailHandler | None = None
        self._task: asyncio.Task[Any] | None = None
        self._running = False
        self._consecutive_errors = 0

    async def start(self) -> None:
        """Initialise the handler and launch the polling loop."""
        if self._running:
            logger.warning("EmailWorker is already running")
            return

        self._handler = EmailHandler(settings=self._settings)
        await self._handler.__aenter__()
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name="email-worker")
        logger.info(
            "EmailWorker started — polling %s every %ds",
            self._target_address,
            self._poll_interval,
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

        logger.info("EmailWorker stopped")

    # ------------------------------------------------------------------
    # Internal polling loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Main loop: fetch → process → sleep → repeat."""
        # Brief startup delay so other services can initialise first
        await asyncio.sleep(5)

        while self._running:
            try:
                await self._poll_once()
                # Reset error counter on success
                self._consecutive_errors = 0
            except asyncio.CancelledError:
                raise
            except Exception:
                self._consecutive_errors += 1
                logger.exception(
                    "Error during email poll cycle (%d/%d consecutive)",
                    self._consecutive_errors,
                    _MAX_CONSECUTIVE_ERRORS,
                )

                # Back off if we're seeing repeated failures
                if self._consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    logger.warning(
                        "Too many consecutive email poll errors — "
                        "backing off for %ds",
                        _BACKOFF_SECONDS,
                    )
                    try:
                        await asyncio.sleep(_BACKOFF_SECONDS)
                    except asyncio.CancelledError:
                        raise
                    self._consecutive_errors = 0
                    continue

            # Sleep until the next cycle (interruptible via cancellation)
            try:
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                raise

    async def _poll_once(self) -> None:
        """Run a single poll-and-process cycle."""
        assert self._handler is not None

        emails = await self._handler.fetch_unread_emails(self._target_address)
        if not emails:
            return

        logger.info("Found %d new email(s) to process", len(emails))

        for email in emails:
            logger.info(
                "Processing email %s from %s — \"%s\"",
                email.message_id,
                email.sender_email,
                email.subject,
            )
            
            # Ingest to Chroma
            self._ingest_to_chroma(email)
            
            try:
                replied = await self._handler.process_email(email)
                if replied:
                    # Swap bark-unread → bark-read ONLY after a reply was sent
                    await self._handler.mark_as_read(email.message_id)
                    logger.info("Successfully processed email %s", email.message_id)
                else:
                    # No reply was sent (bot declined, or generation failed).
                    # Leave the bark-unread label so it's retried / visible.
                    logger.info(
                        "No reply sent for email %s — leaving bark-unread",
                        email.message_id,
                    )
            except Exception:
                logger.exception("Unexpected error processing email %s", email.message_id)

        # Periodic housekeeping
        self._handler.cleanup_old_conversations()

    def _ingest_to_chroma(self, email: Any) -> None:
        """Push parsed email to Chroma for semantic memory and summarization."""
        try:
            from bark.context.chroma import ChromaClient, Document
            from uuid import uuid4
            from datetime import datetime
            
            async def _do_ingest():
                client = ChromaClient(host=self._settings.chroma_host, port=self._settings.chroma_port)
                try:
                    client.connect()
                except Exception:
                    pass
                
                content = f"Subject: {email.subject}\n\n{email.text_body}"
                doc = Document(
                    id=str(uuid4()),
                    content=content,
                    metadata={
                        "source_type": "email",
                        "sender": email.sender_email,
                        "message_id": email.message_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                client.add_documents([doc])
                
            asyncio.create_task(_do_ingest())
        except Exception as e:
            logger.warning(f"Failed to ingest Email to Chroma: {e}")
