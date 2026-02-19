"""
HangHive AI — Summarizer Module
Summarizes conversations and topics using Google Gemini.
"""

from google.genai import types
from app.utils import client, DEFAULT_MODEL, format_response


# ---------------------------------------------------------------------------
# Summarization prompts
# ---------------------------------------------------------------------------

_MESSAGES_SUMMARY_PROMPT = """Summarize the following conversation messages into a concise summary.

Rules:
- Use 3-5 bullet points maximum.
- Capture key topics discussed.
- Mention any decisions or conclusions made.
- Keep it brief and informative.
- Do not add information that wasn't in the messages.

Messages:
{messages}

Provide a clear, concise summary:"""

_TOPIC_SUMMARY_PROMPT = """Summarize the following discussion about "{topic}".

Rules:
- Focus specifically on what was said about the topic.
- Use 3-5 bullet points maximum.
- Highlight key points, agreements, and disagreements.
- Keep it brief and informative.

Messages about "{topic}":
{messages}

Provide a focused summary:"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize_messages(messages: list) -> str:
    """
    Summarize a list of conversation messages.

    Args:
        messages: List of message strings or dicts with 'author' and 'content' keys.

    Returns:
        Summary string.
    """
    if not messages:
        return "No messages to summarize."

    # Format messages
    formatted = []
    for msg in messages:
        if isinstance(msg, dict):
            author = msg.get("author", "User")
            content = msg.get("content", "")
            formatted.append(f"{author}: {content}")
        else:
            formatted.append(str(msg))

    messages_text = "\n".join(formatted)

    if len(messages_text) < 20:
        return "Not enough content to summarize."

    try:
        prompt = _MESSAGES_SUMMARY_PROMPT.format(messages=messages_text)
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are HangHive AI. Provide concise, accurate summaries.",
                temperature=0.3,
                max_output_tokens=512,
            ),
        )
        return format_response(response.text)

    except Exception:
        return "Could not generate summary. Please try again."


def summarize_topic(topic: str, messages: list) -> str:
    """
    Summarize discussion about a specific topic.

    Args:
        topic: The topic to focus on.
        messages: List of message strings or dicts with 'author' and 'content' keys.

    Returns:
        Topic-focused summary string.
    """
    if not messages:
        return "No messages to summarize."

    # Format messages
    formatted = []
    for msg in messages:
        if isinstance(msg, dict):
            author = msg.get("author", "User")
            content = msg.get("content", "")
            formatted.append(f"{author}: {content}")
        else:
            formatted.append(str(msg))

    messages_text = "\n".join(formatted)

    try:
        prompt = _TOPIC_SUMMARY_PROMPT.format(topic=topic, messages=messages_text)
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are HangHive AI. Provide concise, topic-focused summaries.",
                temperature=0.3,
                max_output_tokens=512,
            ),
        )
        return format_response(response.text)

    except Exception:
        return f"Could not generate summary for '{topic}'. Please try again."
