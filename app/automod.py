"""
HANG — Auto-Moderation Module
Automatically detects toxic, spam, and inappropriate messages.
"""

import re
from better_profanity import profanity


# ---------------------------------------------------------------------------
# Initialize profanity filter
# ---------------------------------------------------------------------------
profanity.load_censor_words()


# ---------------------------------------------------------------------------
# Spam detection patterns
# ---------------------------------------------------------------------------

# Excessive repeated characters: "heeeeelllo" or "!!!!!!"
_REPEATED_CHARS = re.compile(r"(.)\1{4,}")

# Excessive mentions: "@everyone @here @user1 @user2 ..."
_MENTION_SPAM = re.compile(r"(@\w+\s*){4,}")

# Common spam link patterns
_LINK_SPAM_PATTERNS = [
    re.compile(r"(https?://\S+\s*){3,}"),          # 3+ links in one message
    re.compile(r"(discord\.gg/|bit\.ly/|tinyurl\.com/)\S+", re.IGNORECASE),
    re.compile(r"free\s+(nitro|gift|steam|robux)", re.IGNORECASE),
    re.compile(r"click\s+here.*http", re.IGNORECASE),
]

# All-caps threshold (more than 70% uppercase and length > 10)
_CAPS_THRESHOLD = 0.7
_CAPS_MIN_LENGTH = 10


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_message(message: str) -> tuple:
    """
    Check a message for violations.

    Args:
        message: The message text to check.

    Returns:
        Tuple of (is_safe: bool, reason: str | None).
        If safe, reason is None.
        If flagged, reason describes the violation.
    """
    if not message or not message.strip():
        return (True, None)

    text = message.strip()

    # 1. Profanity check
    if profanity.contains_profanity(text):
        return (False, "Message contains inappropriate language.")

    # 2. All-caps spam
    if len(text) > _CAPS_MIN_LENGTH:
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if caps_ratio >= _CAPS_THRESHOLD:
                return (False, "Excessive use of capital letters (possible spam).")

    # 3. Repeated characters
    if _REPEATED_CHARS.search(text):
        return (False, "Message contains excessive repeated characters (possible spam).")

    # 4. Mention spam
    if _MENTION_SPAM.search(text):
        return (False, "Too many mentions in a single message (possible spam).")

    # 5. Link spam
    for pattern in _LINK_SPAM_PATTERNS:
        if pattern.search(text):
            return (False, "Suspicious links detected (possible spam).")

    return (True, None)


def censor_message(message: str) -> str:
    """
    Return a censored version of the message with profanity replaced.

    Args:
        message: The message text to censor.

    Returns:
        Censored message string.
    """
    return profanity.censor(message)


def get_violation_level(reason: str) -> str:
    """
    Classify the severity of a violation.

    Args:
        reason: The violation reason string from check_message().

    Returns:
        Severity level: 'low', 'medium', or 'high'.
    """
    if not reason:
        return "none"

    if "inappropriate language" in reason.lower():
        return "high"
    if "suspicious links" in reason.lower():
        return "high"
    if "spam" in reason.lower():
        return "medium"

    return "low"
