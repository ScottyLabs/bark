"""Background summarizer for daily synthesis of ingested documents and messages."""

import asyncio
import logging
from datetime import datetime, timedelta

from bark.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class DailySummarizer:
    """Periodically queries Chroma for recent activity and generates a synthesis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._running = False
        self._task: asyncio.Task | None = None
        # Run every 24 hours
        self._interval = 24 * 60 * 60

    async def start(self) -> None:
        """Start the background summarizing loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="daily-summarizer")
        logger.info("DailySummarizer started — will summarize every 24 hours.")

    async def stop(self) -> None:
        """Stop the background loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("DailySummarizer stopped.")

    async def _loop(self) -> None:
        """Main loop."""
        # Initial sleep so we don't start hammering immediately on boot
        await asyncio.sleep(60)
        
        while self._running:
            try:
                await self.generate_daily_synthesis()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in DailySummarizer: {e}")
                
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                raise

    async def generate_daily_synthesis(self) -> None:
        """Fetch docs from the last 24h and synthesize them."""
        from bark.context.chroma import ChromaClient
        from bark.core.chatbot import ChatBot
        
        client = ChromaClient(host=self.settings.chroma_host, port=self.settings.chroma_port)
        try:
            client.connect()
        except Exception as e:
            logger.warning(f"Summarizer could not connect to Chroma: {e}")
            return
            
        # Get all docs and filter by timestamp metadata down to the last 24 hours
        try:
            results = client._get_or_create_collection().get(include=["metadatas", "documents"])
        except Exception as e:
            logger.warning(f"Error querying Chroma for summarization: {e}")
            return
            
        docs = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        if not docs or not metadatas:
            return
            
        recent_texts = []
        yesterday = datetime.now() - timedelta(hours=24)
        
        for doc, meta in zip(docs, metadatas):
            ts_str = meta.get("timestamp")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str)
                if ts >= yesterday:
                    source = meta.get("source_type", "unknown")
                    recent_texts.append(f"[{source}]: {doc}")
            except Exception:
                pass
                
        if not recent_texts:
            logger.info("No recent activity found for Daily Synthesis.")
            return
            
        # Summarize using ChatBot
        content_to_summarize = "\n\n".join(recent_texts)
        # Prevent token blowup if it was a very busy day
        if len(content_to_summarize) > 50000:
            content_to_summarize = content_to_summarize[:50000] + "\n... (truncated)"
            
        system_prompt = (
            "You are a synthesis agent analyzing the last 24 hours of communications (Slack, Email, Docs). "
            "Write a concise bulleted summary of the key themes, decisions made, and pending questions."
        )
        
        async with ChatBot(settings=self.settings) as bot:
            try:
                summary = await bot.simple_chat(
                    system_prompt + "\n\nCommunications:\n" + content_to_summarize
                )
                
                # Save into the explicit memory tier (filesystem) so it's always injected into standard context
                from bark.memory.memory_system import get_memory_system
                mem = get_memory_system()
                title = f"Daily_Summary_{datetime.now().strftime('%Y-%m-%d')}"
                # Store in admin folder
                mem.write_file("admin", title, f"# Daily Synthesis ({datetime.now().strftime('%Y-%m-%d')})\n\n{summary}")
                logger.info(f"Generated daily synthesis: {title}")
                
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
