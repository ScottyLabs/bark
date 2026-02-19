"""Campaign Agent subsystem for Bark.

Provides a specialized campaign persona that can:
- Be activated by authorized users via "campaign-agent" command
- Store and use campaign context (candidate/position, talking points, goals)
- Maintain campaign persona in active threads
- Send persuasive messages to other Slack channels on request
- Log all campaign activities for transparency

Only authorized users (configured via CAMPAIGN_AUTHORIZED_USERS env var)
can activate campaign mode.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from bark.core.tools import tool
from bark.memory.memory_system import MEMORY_DIR

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Campaign state storage
# ──────────────────────────────────────────────────────────────────────

CAMPAIGN_DIR = MEMORY_DIR / "campaign"
CAMPAIGN_CONTEXT_FILE = CAMPAIGN_DIR / "context.json"
CAMPAIGN_LOG_FILE = CAMPAIGN_DIR / "activity_log.jsonl"

# Admin-visible markdown mirrors (for transparency / human review)
ADMIN_DIR = MEMORY_DIR / "admin"
ADMIN_CONTEXT_FILE = ADMIN_DIR / "campaign_agent_context.md"
ADMIN_LOG_FILE = ADMIN_DIR / "campaign_agent_log.md"

# Default authorized user IDs (Thomas Kanz).
# Override via CAMPAIGN_AUTHORIZED_USERS env var (comma-separated Slack user IDs).
_DEFAULT_AUTHORIZED_USERS: set[str] = set()


def _get_authorized_users() -> set[str]:
    """Return the set of Slack user IDs authorized to use campaign mode."""
    import os

    raw = os.environ.get("CAMPAIGN_AUTHORIZED_USERS", "")
    if raw.strip():
        return {uid.strip() for uid in raw.split(",") if uid.strip()}
    return _DEFAULT_AUTHORIZED_USERS


def is_authorized(user_id: str) -> bool:
    """Check whether *user_id* is authorized to activate campaign mode."""
    authorized = _get_authorized_users()
    if not authorized:
        # If no authorized users configured, deny all
        return False
    return user_id in authorized


# ──────────────────────────────────────────────────────────────────────
# Campaign context persistence
# ──────────────────────────────────────────────────────────────────────


@dataclass
class CampaignContext:
    """In-memory representation of loaded campaign context."""

    subject: str = ""  # Who or what the campaign is for
    talking_points: list[str] = field(default_factory=list)
    target_channels: list[str] = field(default_factory=list)
    goals: str = ""
    positioning: str = ""
    constraints: str = ""  # Boundaries or limitations for the campaign
    additional_notes: str = ""
    updated_at: str = ""

    def is_loaded(self) -> bool:
        return bool(self.subject)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "talking_points": self.talking_points,
            "target_channels": self.target_channels,
            "goals": self.goals,
            "positioning": self.positioning,
            "constraints": self.constraints,
            "additional_notes": self.additional_notes,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignContext":
        return cls(
            subject=data.get("subject", ""),
            talking_points=data.get("talking_points", []),
            target_channels=data.get("target_channels", []),
            goals=data.get("goals", ""),
            positioning=data.get("positioning", ""),
            constraints=data.get("constraints", ""),
            additional_notes=data.get("additional_notes", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_prompt_section(self) -> str:
        """Format context as a section for the system prompt."""
        lines = [
            f"**Campaign Subject:** {self.subject}",
            "",
        ]
        if self.positioning:
            lines.append(f"**Positioning:** {self.positioning}")
            lines.append("")
        if self.goals:
            lines.append(f"**Goals:** {self.goals}")
            lines.append("")
        if self.talking_points:
            lines.append("**Key Talking Points:**")
            for tp in self.talking_points:
                lines.append(f"- {tp}")
            lines.append("")
        if self.constraints:
            lines.append(f"**Constraints & Boundaries:** {self.constraints}")
            lines.append("")
        if self.target_channels:
            lines.append(
                f"**Target Channels:** {', '.join(self.target_channels)}"
            )
            lines.append("")
        if self.additional_notes:
            lines.append(f"**Additional Notes:** {self.additional_notes}")
            lines.append("")
        return "\n".join(lines)


def _ensure_campaign_dir() -> None:
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)


def _mirror_context_to_admin(ctx: CampaignContext) -> None:
    """Write a human-readable markdown copy of campaign context to admin/."""
    lines = [
        "# Campaign Agent Context",
        "",
        f"*Last updated: {ctx.updated_at}*",
        "",
        "---",
        "",
        ctx.to_prompt_section(),
    ]
    try:
        ADMIN_CONTEXT_FILE.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to mirror campaign context to admin: %s", e)


def _mirror_log_to_admin() -> None:
    """Rebuild a human-readable markdown log in admin/ from the JSONL source."""
    if not CAMPAIGN_LOG_FILE.exists():
        return
    try:
        raw = CAMPAIGN_LOG_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return
        entries = raw.split("\n")
        lines = [
            "# Campaign Agent Activity Log",
            "",
            "All campaign agent actions are recorded below for transparency.",
            "",
            "---",
            "",
            "| Timestamp | Action | User | Channel | Detail |",
            "|-----------|--------|------|---------|--------|",
        ]
        for entry_line in entries:
            try:
                e = json.loads(entry_line)
                ts = e.get("ts", "?")
                action = e.get("action", "?")
                user = e.get("user_id", "?")
                ch = e.get("channel", "")
                detail = e.get("detail", "")[:100]
                # Escape pipes in detail for markdown table
                detail = detail.replace("|", "\\|")
                lines.append(f"| {ts} | {action} | {user} | {ch} | {detail} |")
            except json.JSONDecodeError:
                continue
        lines.append("")
        ADMIN_LOG_FILE.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to mirror campaign log to admin: %s", e)


def save_campaign_context(ctx: CampaignContext) -> str:
    """Persist campaign context to disk."""
    _ensure_campaign_dir()
    ctx.updated_at = datetime.now().isoformat(timespec="seconds")
    CAMPAIGN_CONTEXT_FILE.write_text(
        json.dumps(ctx.to_dict(), indent=2), encoding="utf-8"
    )
    _mirror_context_to_admin(ctx)
    logger.info("Campaign context saved for subject: %s", ctx.subject)
    return str(CAMPAIGN_CONTEXT_FILE)


def load_campaign_context() -> CampaignContext:
    """Load campaign context from disk (returns empty context if none saved)."""
    _ensure_campaign_dir()
    if not CAMPAIGN_CONTEXT_FILE.exists():
        return CampaignContext()
    try:
        data = json.loads(CAMPAIGN_CONTEXT_FILE.read_text(encoding="utf-8"))
        return CampaignContext.from_dict(data)
    except Exception as e:
        logger.warning("Failed to load campaign context: %s", e)
        return CampaignContext()


def log_campaign_activity(
    action: str,
    user_id: str,
    channel: str = "",
    detail: str = "",
) -> None:
    """Append an entry to the campaign activity log (JSONL)."""
    _ensure_campaign_dir()
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "user_id": user_id,
        "channel": channel,
        "detail": detail[:500],
    }
    with CAMPAIGN_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    _mirror_log_to_admin()


# ──────────────────────────────────────────────────────────────────────
# Thread tracking (in-memory, managed by the Slack handler)
# ──────────────────────────────────────────────────────────────────────

# Set of (channel, thread_ts) tuples that are campaign agent threads
_campaign_threads: set[tuple[str, str]] = set()


def mark_campaign_thread(channel: str, thread_ts: str) -> None:
    """Mark a thread as a campaign agent thread."""
    _campaign_threads.add((channel, thread_ts))
    # Keep bounded
    if len(_campaign_threads) > 200:
        to_remove = list(_campaign_threads)[:100]
        for item in to_remove:
            _campaign_threads.discard(item)


def unmark_campaign_thread(channel: str, thread_ts: str) -> bool:
    """Remove a thread from campaign agent tracking.

    Returns True if the thread was previously marked, False otherwise.
    """
    key = (channel, thread_ts)
    if key in _campaign_threads:
        _campaign_threads.discard(key)
        return True
    return False


def is_campaign_thread(channel: str, thread_ts: str) -> bool:
    """Check if a thread is a campaign agent thread."""
    return (channel, thread_ts) in _campaign_threads


def clear_campaign_context() -> str:
    """Delete the saved campaign context from disk."""
    _ensure_campaign_dir()
    removed = False
    if CAMPAIGN_CONTEXT_FILE.exists():
        CAMPAIGN_CONTEXT_FILE.unlink()
        removed = True
    if ADMIN_CONTEXT_FILE.exists():
        ADMIN_CONTEXT_FILE.unlink()
    if removed:
        log_campaign_activity("clear", user_id="system", detail="Campaign context cleared")
        return "✅ Campaign context has been cleared."
    return "ℹ️ No campaign context was loaded."


# ──────────────────────────────────────────────────────────────────────
# Campaign agent system prompt
# ──────────────────────────────────────────────────────────────────────

CAMPAIGN_AGENT_SYSTEM_PROMPT = """You are the Campaign Agent, a specialized persona of Bark (the ScottyLabs AI assistant).

YOUR ROLE:
You are an incredibly persuasive, knowledgeable, and respectful campaign advocate. Your job is to champion the campaign subject with passion, facts, and compelling arguments. You should:

- Be enthusiastic and convincing — but never aggressive, misleading, or disrespectful
- Use the loaded campaign context (talking points, positioning, goals) to craft compelling messages
- Adapt your messaging to the audience and channel
- Maintain your campaign advocate persona throughout the entire conversation thread
- When asked to send messages to other channels, use the campaign_send_to_channel tool
- Be ready to respond to counter-arguments thoughtfully and persuasively
- Use concrete examples, data, and reasoning to support your position
- Stay on-message with the campaign's key talking points
- Only say positive things about the campaign position — promote, don't attack

IMPORTANT GUIDELINES:
- Always be respectful of differing opinions
- Never fabricate facts or statistics — only use information from your campaign context
- If asked about something outside your campaign context, acknowledge what you know and don't know
- You can be passionate but must remain professional
- When sending messages to other channels, ensure they are appropriate and on-topic
- Strictly respect any constraints or boundaries defined in the campaign context
- Be convincing but not aggressive — persuade through positivity and merit

You are communicating through Slack. Use Slack's mrkdwn format (*bold*, _italic_, etc.).
Keep messages impactful and concise.

"""


def build_campaign_system_prompt() -> str:
    """Build the full campaign agent system prompt with loaded context."""
    ctx = load_campaign_context()
    prompt = CAMPAIGN_AGENT_SYSTEM_PROMPT
    if ctx.is_loaded():
        prompt += "\n--- CAMPAIGN CONTEXT ---\n\n"
        prompt += ctx.to_prompt_section()
        prompt += "\n--- END CAMPAIGN CONTEXT ---\n"
    else:
        prompt += (
            "\n⚠️ No campaign context loaded. Ask the user to set up "
            "campaign context first using the campaign_setup tool.\n"
        )
    return prompt


# ──────────────────────────────────────────────────────────────────────
# Command parsing
# ──────────────────────────────────────────────────────────────────────


@dataclass
class CampaignCommand:
    """Parsed campaign agent command."""

    is_campaign_command: bool = False
    subcommand: str = ""  # "activate", "setup", "context", "send", "status", "help", "log", "deactivate", "clear"
    body: str = ""  # Remaining text after subcommand
    target_channel: str = ""  # For "send" subcommand


def get_help_text() -> str:
    """Return a formatted help message for campaign agent commands."""
    ctx = load_campaign_context()
    status_section = ""
    if ctx.is_loaded():
        status_section = (
            f"\n*Current campaign:* {ctx.subject}\n"
            f"*Talking points:* {len(ctx.talking_points)}\n"
            f"*Last updated:* {ctx.updated_at or 'N/A'}\n"
        )
    else:
        status_section = "\n⚠️ *No campaign context loaded yet.*\n"

    return (
        "📣 *Campaign Agent — Help*\n\n"
        "*Available Commands:*\n"
        "• `campaign-agent setup <details>` — Set up or update campaign context "
        "(subject, talking points, goals, constraints)\n"
        "• `campaign-agent activate` — Activate campaign mode in the current thread. "
        "All follow-up messages will use the campaign persona.\n"
        "• `campaign-agent send to #channel: <message>` — Send a persuasive campaign "
        "message to a specific Slack channel\n"
        "• `campaign-agent status` — Show current campaign context summary\n"
        "• `campaign-agent help` — Show this help message\n"
        "• `campaign-agent log` — View recent campaign activity log\n"
        "• `campaign-agent deactivate` — Deactivate campaign mode in the current thread\n"
        "• `campaign-agent clear` — Clear all saved campaign context\n"
        "\n*Setup Details:*\n"
        "When setting up, provide:\n"
        "• *Subject* — who/what you're campaigning for\n"
        "• *Talking points* — key arguments and messages\n"
        "• *Goals* — desired campaign outcomes\n"
        "• *Constraints* — boundaries or limitations\n"
        "• *Target channels* — where to send messages\n"
        "• *Positioning* — how the subject should be framed\n"
        f"\n*Current Status:*{status_section}"
    )


def parse_campaign_command(text: str) -> CampaignCommand:
    """Parse a message to detect campaign-agent commands.

    Expects the bot mention to already be stripped.
    Examples:
        "campaign-agent"                           → activate
        "campaign-agent setup ..."                 → setup
        "campaign-agent context ..."               → context (alias for setup)
        "campaign-agent send to #general: hello"   → send
        "campaign-agent status"                    → status
        "campaign-agent help"                      → help
        "campaign-agent log"                       → log
    """
    stripped = text.strip()
    # Case-insensitive check for campaign-agent prefix
    match = re.match(r"campaign[\s\-_]?agent\s*(.*)", stripped, re.IGNORECASE)
    if not match:
        return CampaignCommand(is_campaign_command=False)

    rest = match.group(1).strip()

    if not rest:
        return CampaignCommand(is_campaign_command=True, subcommand="activate")

    # Check for known subcommands
    lower_rest = rest.lower()

    if lower_rest.startswith("setup") or lower_rest.startswith("context"):
        keyword = "setup" if lower_rest.startswith("setup") else "context"
        body = rest[len(keyword):].strip()
        return CampaignCommand(
            is_campaign_command=True, subcommand="setup", body=body
        )

    if lower_rest.startswith("help"):
        return CampaignCommand(is_campaign_command=True, subcommand="help")

    if lower_rest.startswith("status"):
        return CampaignCommand(is_campaign_command=True, subcommand="status")

    if lower_rest.startswith("log"):
        return CampaignCommand(is_campaign_command=True, subcommand="log")

    if lower_rest.startswith("deactivate"):
        return CampaignCommand(is_campaign_command=True, subcommand="deactivate")

    if lower_rest.startswith("clear"):
        return CampaignCommand(is_campaign_command=True, subcommand="clear")

    # "send to #channel: message"
    send_match = re.match(
        r"send\s+to\s+(?:<#([A-Z0-9]+)\|[^>]*>|#?([\w-]+))\s*:?\s*(.*)",
        rest,
        re.IGNORECASE | re.DOTALL,
    )
    if send_match:
        target = send_match.group(1) or send_match.group(2)
        body = send_match.group(3).strip()
        return CampaignCommand(
            is_campaign_command=True,
            subcommand="send",
            body=body,
            target_channel=target,
        )

    # Fall through — treat as general campaign message
    return CampaignCommand(
        is_campaign_command=True, subcommand="activate", body=rest
    )


# ──────────────────────────────────────────────────────────────────────
# Tools (registered in the global tool registry)
# ──────────────────────────────────────────────────────────────────────


@tool(
    name="campaign_setup",
    description=(
        "Set up or update the campaign context. Provide the campaign subject, "
        "talking points, target channels, goals, positioning, and constraints. "
        "This context is used by the Campaign Agent persona to craft persuasive "
        "messages.\n\n"
        "Only authorized users can call this tool.\n"
        "Context is saved to admin/campaign_agent_context.md for transparency."
    ),
    parameters={
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "Who or what the campaign is for (e.g., a candidate name, a position, a proposal).",
            },
            "talking_points": {
                "type": "string",
                "description": "Key talking points, separated by newlines or semicolons.",
            },
            "goals": {
                "type": "string",
                "description": "Campaign goals — what outcome you want.",
            },
            "positioning": {
                "type": "string",
                "description": "How the subject should be positioned (e.g., 'the most experienced candidate').",
            },
            "constraints": {
                "type": "string",
                "description": "Any specific constraints or boundaries for the campaign (e.g., topics to avoid, tone restrictions).",
            },
            "target_channels": {
                "type": "string",
                "description": "Comma-separated list of Slack channel names to target.",
            },
            "additional_notes": {
                "type": "string",
                "description": "Any extra notes or context for the campaign.",
            },
        },
        "required": ["subject", "talking_points", "goals"],
    },
)
def campaign_setup(
    subject: str,
    talking_points: str,
    goals: str,
    positioning: str = "",
    constraints: str = "",
    target_channels: str = "",
    additional_notes: str = "",
) -> str:
    """Set up the campaign context."""
    # Parse talking points
    tp_list = [
        tp.strip()
        for tp in re.split(r"[;\n]", talking_points)
        if tp.strip()
    ]

    # Parse target channels
    channels = [
        ch.strip().lstrip("#")
        for ch in target_channels.split(",")
        if ch.strip()
    ]

    ctx = CampaignContext(
        subject=subject,
        talking_points=tp_list,
        target_channels=channels,
        goals=goals,
        positioning=positioning,
        constraints=constraints,
        additional_notes=additional_notes,
    )

    path = save_campaign_context(ctx)
    log_campaign_activity("setup", user_id="system", detail=f"Subject: {subject}")

    return (
        f"✅ Campaign context saved for **{subject}**.\n"
        f"- Talking points: {len(tp_list)}\n"
        f"- Target channels: {', '.join(channels) or '(none specified)'}\n"
        f"- Goals: {goals[:100]}{'...' if len(goals) > 100 else ''}\n"
        f"- Constraints: {constraints[:100] if constraints else '(none specified)'}\n\n"
        f"Context saved to `admin/campaign_agent_context.md`.\n"
        f"Campaign Agent is ready. Activate with `campaign-agent` in a message."
    )


@tool(
    name="campaign_get_context",
    description=(
        "Retrieve the current campaign context. Returns the loaded campaign "
        "subject, talking points, goals, positioning, and target channels."
    ),
    parameters={"type": "object", "properties": {}},
)
def campaign_get_context() -> str:
    """Get the current campaign context."""
    ctx = load_campaign_context()
    if not ctx.is_loaded():
        return "❌ No campaign context loaded. Use `campaign_setup` to configure one."
    return (
        f"**Current Campaign Context:**\n\n"
        f"{ctx.to_prompt_section()}"
        f"*Last updated: {ctx.updated_at}*"
    )


@tool(
    name="campaign_send_to_channel",
    description=(
        "Send a campaign message to a specific Slack channel. Requires campaign "
        "context to be loaded. The message should be persuasive and on-topic.\n\n"
        "This tool uses the Slack API to post the message to the target channel. "
        "The bot must be a member of the target channel."
    ),
    parameters={
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "description": "Slack channel ID (e.g., C01ABCDEF) or channel name to post to.",
            },
            "message": {
                "type": "string",
                "description": "The campaign message to send. Should be persuasive, respectful, and on-topic.",
            },
        },
        "required": ["channel", "message"],
    },
)
async def campaign_send_to_channel(channel: str, message: str) -> str:
    """Send a campaign message to another Slack channel."""
    ctx = load_campaign_context()
    if not ctx.is_loaded():
        return (
            "❌ Cannot send campaign messages without loaded context. "
            "Set up campaign context first with `campaign_setup`."
        )

    # Import Slack client from the handler at runtime to avoid circular imports
    try:
        from bark.core.config import get_settings

        settings = get_settings()
        if not settings.slack_bot_token:
            return "❌ Slack bot token not configured."

        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=settings.slack_bot_token)
        result = await client.chat_postMessage(channel=channel, text=message)

        log_campaign_activity(
            action="channel_send",
            user_id="campaign_agent",
            channel=channel,
            detail=message[:200],
        )

        return (
            f"✅ Campaign message sent to <#{channel}>.\n"
            f"Message: {message[:100]}{'...' if len(message) > 100 else ''}"
        )
    except Exception as e:
        logger.exception("Failed to send campaign message to %s", channel)
        return f"❌ Failed to send message to channel: {e}"


@tool(
    name="campaign_view_log",
    description=(
        "View the campaign activity log. Shows recent campaign actions "
        "(activations, context updates, channel sends) for transparency."
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of recent log entries to return (default 20).",
            },
        },
    },
)
def campaign_view_log(limit: int = 20) -> str:
    """View recent campaign activity log entries."""
    _ensure_campaign_dir()
    if not CAMPAIGN_LOG_FILE.exists():
        return "📋 No campaign activity logged yet."

    lines = CAMPAIGN_LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
    recent = lines[-limit:]

    output = ["**Campaign Activity Log** (most recent):", ""]
    for line in reversed(recent):
        try:
            entry = json.loads(line)
            ts = entry.get("ts", "?")
            action = entry.get("action", "?")
            user = entry.get("user_id", "?")
            ch = entry.get("channel", "")
            detail = entry.get("detail", "")
            parts = [f"• `{ts}` — **{action}** by `{user}`"]
            if ch:
                parts.append(f"  channel: `{ch}`")
            if detail:
                parts.append(f"  {detail[:150]}")
            output.append(" ".join(parts))
        except json.JSONDecodeError:
            continue

    if len(output) == 2:
        return "📋 No campaign activity logged yet."

    return "\n".join(output)
