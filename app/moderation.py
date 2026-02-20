"""
HANG — Moderation Commands Module
Handles manual moderation actions: warn, mute, kick, ban.
Designed for use with discord.py but keeps logic decoupled.
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# In-memory warning tracker (replace with DB in production)
# ---------------------------------------------------------------------------
_warnings = {}  # {user_id: [{"reason": ..., "moderator": ..., "timestamp": ...}, ...]}


# ---------------------------------------------------------------------------
# Warning System
# ---------------------------------------------------------------------------

def warn_user(user_id: str, user_name: str, reason: str, moderator: str) -> dict:
    """
    Issue a warning to a user.

    Args:
        user_id: Unique identifier of the user.
        user_name: Display name of the user.
        reason: Reason for the warning.
        moderator: Name of the moderator issuing the warning.

    Returns:
        Warning record dict with count info.
    """
    if user_id not in _warnings:
        _warnings[user_id] = []

    warning = {
        "reason": reason,
        "moderator": moderator,
        "timestamp": datetime.now().isoformat(),
    }
    _warnings[user_id].append(warning)

    count = len(_warnings[user_id])

    return {
        "action": "warn",
        "user": user_name,
        "user_id": user_id,
        "reason": reason,
        "moderator": moderator,
        "warning_count": count,
        "message": f"⚠️ {user_name} has been warned. Reason: {reason} (Warning #{count})",
    }


def get_warnings(user_id: str) -> list:
    """Get all warnings for a user."""
    return _warnings.get(user_id, [])


def clear_warnings(user_id: str) -> int:
    """Clear all warnings for a user. Returns the count cleared."""
    count = len(_warnings.get(user_id, []))
    _warnings.pop(user_id, None)
    return count


# ---------------------------------------------------------------------------
# Mute / Timeout
# ---------------------------------------------------------------------------

def mute_user(user_name: str, duration_minutes: int, reason: str, moderator: str) -> dict:
    """
    Generate mute action record.
    Actual Discord muting must be done in main.py using the member object.

    Args:
        user_name: Display name of the user.
        duration_minutes: Duration of the mute in minutes.
        reason: Reason for the mute.
        moderator: Name of the moderator.

    Returns:
        Mute action record dict.
    """
    duration = timedelta(minutes=duration_minutes)

    return {
        "action": "mute",
        "user": user_name,
        "duration_minutes": duration_minutes,
        "duration_timedelta": duration,
        "reason": reason,
        "moderator": moderator,
        "message": f"🔇 {user_name} has been muted for {duration_minutes} minutes. Reason: {reason}",
    }


# ---------------------------------------------------------------------------
# Kick
# ---------------------------------------------------------------------------

def kick_user(user_name: str, reason: str, moderator: str) -> dict:
    """
    Generate kick action record.
    Actual Discord kicking must be done in main.py using the member object.

    Args:
        user_name: Display name of the user.
        reason: Reason for the kick.
        moderator: Name of the moderator.

    Returns:
        Kick action record dict.
    """
    return {
        "action": "kick",
        "user": user_name,
        "reason": reason,
        "moderator": moderator,
        "message": f"👢 {user_name} has been kicked. Reason: {reason}",
    }


# ---------------------------------------------------------------------------
# Ban
# ---------------------------------------------------------------------------

def ban_user(user_name: str, reason: str, moderator: str) -> dict:
    """
    Generate ban action record.
    Actual Discord banning must be done in main.py using the member object.

    Args:
        user_name: Display name of the user.
        reason: Reason for the ban.
        moderator: Name of the moderator.

    Returns:
        Ban action record dict.
    """
    return {
        "action": "ban",
        "user": user_name,
        "reason": reason,
        "moderator": moderator,
        "message": f"🔨 {user_name} has been banned. Reason: {reason}",
    }


# ---------------------------------------------------------------------------
# Mod Log Formatter
# ---------------------------------------------------------------------------

def get_mod_log(action: str, moderator: str, target: str, reason: str) -> str:
    """
    Format a moderation action as a log entry.

    Args:
        action: Action type (warn/mute/kick/ban).
        moderator: Moderator who performed the action.
        target: Target user.
        reason: Reason for the action.

    Returns:
        Formatted log string.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"[{timestamp}] MOD ACTION: {action.upper()}\n"
        f"  Moderator: {moderator}\n"
        f"  Target: {target}\n"
        f"  Reason: {reason}"
    )
