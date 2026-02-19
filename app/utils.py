"""
HangHive AI — Utilities & Configuration
Shared helpers, config loading, and Gemini client initialization.
"""

import os
import re
from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add your Gemini API key to the .env file."
    )

# ---------------------------------------------------------------------------
# Configure Gemini client
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Community types
# ---------------------------------------------------------------------------
COMMUNITY_TYPES = ["study", "coding", "professional", "casual", "general"]

def validate_community_type(community_type: str) -> str:
    """Validate and return a valid community type; defaults to 'general'."""
    ct = community_type.strip().lower()
    if ct in COMMUNITY_TYPES:
        return ct
    return "general"

# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

_STUDY_KEYWORDS = [
    "explain", "what is", "define", "difference between", "how does",
    "formula", "theorem", "equation", "concept", "theory", "homework",
    "assignment", "exam", "study", "learn", "chapter", "subject",
    "biology", "physics", "chemistry", "math", "history", "geography",
]

_CODING_KEYWORDS = [
    "code", "function", "error", "bug", "debug", "python", "java",
    "javascript", "html", "css", "react", "node", "api", "database",
    "sql", "algorithm", "loop", "array", "class", "object", "syntax",
    "compile", "runtime", "import", "library", "framework", "git",
    "deploy", "server", "frontend", "backend", "stack",
]

_PROFESSIONAL_KEYWORDS = [
    "meeting", "deadline", "report", "proposal", "client", "project",
    "budget", "strategy", "presentation", "quarterly", "stakeholder",
    "business", "enterprise", "corporate", "management", "kpi",
    "performance review", "agenda", "professional",
]

def detect_intent(message: str) -> str:
    """
    Classify intent based on keywords.
    Returns one of: 'study', 'coding', 'professional', 'casual', 'general'.
    """
    msg = message.lower()

    coding_score = sum(1 for kw in _CODING_KEYWORDS if kw in msg)
    study_score = sum(1 for kw in _STUDY_KEYWORDS if kw in msg)
    prof_score = sum(1 for kw in _PROFESSIONAL_KEYWORDS if kw in msg)

    scores = {
        "coding": coding_score,
        "study": study_score,
        "professional": prof_score,
    }

    best = max(scores, key=scores.get)
    if scores[best] >= 1:
        return best

    # Check for casual patterns
    casual_patterns = [
        r"\b(lol|haha|lmao|bruh|bro|dude|yo|sup|hey|hi|hello)\b",
        r"[!?]{2,}",
        r"(😂|😎|🔥|💀|🤣|😁|👋)",
    ]
    for pattern in casual_patterns:
        if re.search(pattern, msg):
            return "casual"

    return "general"

# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def format_response(text: str) -> str:
    """Clean up AI output — trim whitespace, remove artifacts."""
    if not text:
        return "I'm sorry, I couldn't generate a response. Please try again."

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove any "HangHive AI:" prefix the model might add
    prefixes_to_remove = [
        "HangHive AI:",
        "HangHive AI :",
        "Assistant:",
        "Bot:",
    ]
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    return text
