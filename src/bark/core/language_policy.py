"""Japanese language policy compliance check for outgoing messages.

Detects Japanese characters (hiragana, katakana, kanji) in text and applies
a configurable policy (``allow`` / ``warn`` / ``strict``):

- **allow**: No filtering; Japanese content passes through silently.
- **warn** (default): Japanese content is allowed, but a warning is logged.
- **strict**: Messages containing Japanese characters are blocked and
  replaced with a fallback notice.

The policy is intentionally limited to *outgoing bot responses*.  Incoming
user messages are never blocked — only logged if they contain Japanese.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unicode ranges for Japanese script detection
# ---------------------------------------------------------------------------
# Hiragana:         U+3040 – U+309F
# Katakana:         U+30A0 – U+30FF
# CJK Unified (Kanji): U+4E00 – U+9FFF
# Katakana Half-Width:  U+FF65 – U+FF9F

_JAPANESE_PATTERN = re.compile(
    r"[\u3040-\u309F"   # Hiragana
    r"\u30A0-\u30FF"    # Katakana
    r"\u4E00-\u9FFF"    # CJK Unified Ideographs (Kanji)
    r"\uFF65-\uFF9F]",  # Katakana Half-Width
)


class PolicyMode(str, Enum):
    """Valid language-policy modes."""

    ALLOW = "allow"
    WARN = "warn"
    STRICT = "strict"


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def contains_japanese(text: str) -> bool:
    """Return True if *text* contains any Japanese characters."""
    return bool(_JAPANESE_PATTERN.search(text))


def japanese_char_count(text: str) -> int:
    """Return the number of Japanese characters in *text*."""
    return len(_JAPANESE_PATTERN.findall(text))


def japanese_ratio(text: str) -> float:
    """Return the ratio of Japanese characters to total characters.

    Returns 0.0 for empty strings.
    """
    if not text:
        return 0.0
    return japanese_char_count(text) / len(text)


# ---------------------------------------------------------------------------
# Policy result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolicyResult:
    """Outcome of a language-policy check."""

    allowed: bool
    """Whether the message should be sent."""

    original_text: str
    """The text that was checked."""

    filtered_text: str
    """Text to actually send (may differ from *original_text* in strict mode)."""

    japanese_detected: bool
    """Whether any Japanese characters were found."""

    char_count: int
    """Number of Japanese characters detected."""

    mode: str
    """The policy mode that was applied."""


# ---------------------------------------------------------------------------
# Core policy check
# ---------------------------------------------------------------------------

_STRICT_FALLBACK = (
    "[This response was blocked by the language policy because it "
    "contained Japanese characters.  Please rephrase in English.]"
)


def check_language_policy(
    text: str,
    mode: str = "warn",
) -> PolicyResult:
    """Validate *text* against the Japanese-language policy.

    Parameters
    ----------
    text:
        The outgoing message to check.
    mode:
        One of ``"allow"``, ``"warn"``, or ``"strict"``.
        Defaults to ``"warn"`` (log but allow).

    Returns
    -------
    PolicyResult
        Contains the decision, the (possibly replaced) text, and metadata.
    """
    # Normalise mode to lowercase; fall back to "warn" on bad values
    mode = mode.strip().lower()
    if mode not in {m.value for m in PolicyMode}:
        logger.warning(
            "Invalid JAPANESE_LANGUAGE_POLICY mode %r — falling back to 'warn'",
            mode,
        )
        mode = PolicyMode.WARN.value

    detected = contains_japanese(text)
    count = japanese_char_count(text) if detected else 0

    if not detected:
        return PolicyResult(
            allowed=True,
            original_text=text,
            filtered_text=text,
            japanese_detected=False,
            char_count=0,
            mode=mode,
        )

    # Japanese was found — act according to mode
    if mode == PolicyMode.ALLOW.value:
        # Silently allow
        return PolicyResult(
            allowed=True,
            original_text=text,
            filtered_text=text,
            japanese_detected=True,
            char_count=count,
            mode=mode,
        )

    if mode == PolicyMode.WARN.value:
        logger.warning(
            "Japanese content detected in outgoing message "
            "(%d chars, ratio=%.2f). Policy mode is 'warn' — allowing.",
            count,
            japanese_ratio(text),
        )
        return PolicyResult(
            allowed=True,
            original_text=text,
            filtered_text=text,
            japanese_detected=True,
            char_count=count,
            mode=mode,
        )

    # strict mode — block the message
    logger.warning(
        "Japanese content BLOCKED in outgoing message "
        "(%d chars, ratio=%.2f). Policy mode is 'strict'.",
        count,
        japanese_ratio(text),
    )
    return PolicyResult(
        allowed=False,
        original_text=text,
        filtered_text=_STRICT_FALLBACK,
        japanese_detected=True,
        char_count=count,
        mode=mode,
    )


# ---------------------------------------------------------------------------
# Convenience wrapper used by the response pipeline
# ---------------------------------------------------------------------------

def apply_language_policy(text: str, mode: str = "warn") -> str:
    """Check *text* and return the text that should actually be sent.

    This is the main entry-point for the response pipeline.  It runs the
    policy check and returns either the original text (allow/warn) or the
    fallback string (strict).
    """
    result = check_language_policy(text, mode=mode)
    return result.filtered_text
