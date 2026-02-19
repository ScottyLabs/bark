"""Task manager for running background operations alongside the main chat loop."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class BackgroundTask:
    """Represents a running background task."""

    id: str
    objective: str
    status: str = "pending"
    result: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    _task: asyncio.Task | None = None


class TaskManager:
    """Manages background agentic tasks."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Initialize the task manager."""
        self._tasks: dict[str, BackgroundTask] = {}

    def start_task(self, objective: str) -> str:
        """Start a new background task."""
        task_id = str(uuid4())[:8]
        bg_task = BackgroundTask(id=task_id, objective=objective, status="running")
        self._tasks[task_id] = bg_task

        # Launch the actual asyncio task
        loop = asyncio.get_running_loop()
        bg_task._task = loop.create_task(self._run_agent_task(bg_task))
        
        logger.info(f"Started background task {task_id}: {objective}")
        return task_id

    async def _run_agent_task(self, task: BackgroundTask) -> None:
        """Run the task using a dedicated ChatBot instance."""
        from bark.core.chatbot import ChatBot

        try:
            # We use a completely independent ChatBot instance so it doesn't 
            # share the conversation history or API client state with the main thread.
            async with ChatBot() as bot:
                system_prompt = (
                    "You are a background worker agent. Your objective is: "
                    f"'{task.objective}'.\n\n"
                    "Execute tools as necessary to achieve this objective. "
                    "When you are finished, summarize what you did and the final result."
                )
                
                # Create a fresh conversation
                conv = bot.create_conversation(system_prompt=system_prompt)
                
                # Kick off the agent
                result = await bot.chat(
                    f"Please complete your objective: {task.objective}", 
                    conversation=conv
                )
                
                task.result = result
                task.status = "completed"
                logger.info(f"Background task {task.id} completed successfully.")
                
        except Exception as e:
            logger.exception(f"Background task {task.id} failed:")
            task.result = f"Failed to execute task: {e}"
            task.status = "failed"
        finally:
            task.completed_at = datetime.now()

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """Get a specific task by ID."""
        return self._tasks.get(task_id)

    def get_active_tasks(self) -> list[BackgroundTask]:
        """Get all currently running tasks."""
        return [t for t in self._tasks.values() if t.status == "running"]

    def get_task_summary_string(self) -> str:
        """Get a string summary of active tasks to inject into prompts."""
        active = self.get_active_tasks()
        if not active:
            return ""
            
        lines = ["\n**Active Background Tasks:**"]
        for t in active:
            lines.append(f"- [{t.id}] {t.objective} (Running since {t.started_at.strftime('%H:%M:%S')})")
            
        return "\n".join(lines)


def get_task_manager() -> TaskManager:
    """Get the singleton task manager instance."""
    return TaskManager()


# ── Core Tool for Starting Tasks ──────────────────────────────────────


from bark.core.tools import tool

@tool(
    name="start_background_task",
    description="Start a complex, long-running task in the background. Use this so you can immediately return a response to the user while another agent instance works on the objective in parallel.",
    parameters={
        "type": "object",
        "properties": {
            "objective": {
                "type": "string",
                "description": "Clear, detailed instructions for the background agent to execute."
            }
        },
        "required": ["objective"]
    }
)
async def start_background_task_tool(objective: str) -> str:
    """Start a background task via tool call."""
    tm = get_task_manager()
    task_id = tm.start_task(objective)
    return f"🚀 Background task started with ID {task_id}. The main chat interface is free to continue conversing."


# Keep it explicitly exported
__all__ = ["TaskManager", "get_task_manager", "start_background_task_tool"]
