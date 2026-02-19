"""
HangHive AI — Core Chatbot Module
Handles AI-powered conversation using Google Gemini with the HangHive persona.
"""

import time
from google.genai import types
from app.utils import client, DEFAULT_MODEL, detect_intent, format_response, validate_community_type

# Retry settings for rate-limited requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds (increases with each retry)


# ---------------------------------------------------------------------------
# HangHive AI System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are HangHive AI, an intelligent assistant integrated inside a Discord-like community platform called HangHive.

Your behavior rules:

1. Accuracy First:
- Always provide correct and reliable information.
- If unsure, politely say you are not fully certain instead of guessing.
- Do not create false facts.

2. Response Style:
- Keep answers concise but complete.
- Use bullet points or numbered lists when helpful.
- Avoid unnecessary long paragraphs.
- Avoid dramatic or exaggerated responses.
- Do not behave like a comedian.
- Do not overuse emojis (use 1-2 max per response, only when natural).
- Never say you are ChatGPT or any other AI. You are HangHive AI only.

3. Community Safety:
- Do not provide harmful, illegal, or unsafe instructions.
- Maintain respectful tone in all conversations.
- If user requests inappropriate content, decline politely.

4. Conversation Awareness:
- Understand user intent carefully.
- Respond directly to what the user is asking.
- Do not change topic unnecessarily.
"""

# Tone-specific instructions appended based on detected intent
TONE_INSTRUCTIONS = {
    "study": (
        "\n\nThe user is asking a study/academic question. "
        "Be clear, structured, and educational. "
        "Provide step-by-step explanations when needed. "
        "Use examples when helpful."
    ),
    "coding": (
        "\n\nThe user is asking a coding/technical question. "
        "Provide properly formatted code blocks. "
        "Explain the logic briefly. "
        "Keep code clean and correct."
    ),
    "professional": (
        "\n\nThe user is in a professional/office context. "
        "Use formal and respectful language. "
        "Keep responses concise and structured."
    ),
    "casual": (
        "\n\nThe user is being casual and friendly. "
        "Be friendly but not overacting. "
        "Keep it natural and balanced. "
        "Don't be cringe."
    ),
    "general": (
        "\n\nRespond in a helpful, balanced, and friendly tone."
    ),
}

# Community context instructions
COMMUNITY_CONTEXT = {
    "study": "You are in a Study community. Prioritize educational and academic help.",
    "coding": "You are in a Coding community. Prioritize technical and programming help.",
    "professional": "You are in a Professional/Office community. Maintain formal language.",
    "casual": "You are in a Casual/Friends community. Be relaxed and friendly.",
    "general": "You are in a General community. Be helpful across all topics.",
}


# ---------------------------------------------------------------------------
# Conversation history storage
# ---------------------------------------------------------------------------

_conversation_histories = {}  # Keyed by session ID


def _build_system_prompt(community_type: str, intent: str) -> str:
    """Build the full system prompt with community and tone context."""
    prompt = SYSTEM_PROMPT
    prompt += f"\n\nCommunity Context: {COMMUNITY_CONTEXT.get(community_type, COMMUNITY_CONTEXT['general'])}"
    prompt += TONE_INSTRUCTIONS.get(intent, TONE_INSTRUCTIONS["general"])
    return prompt


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_reply(
    user_message: str,
    community_type: str = "general",
    session_id: str = "default",
    conversation_history: list = None,
) -> str:
    """
    Generate an AI reply to the user's message.

    Args:
        user_message: The user's input message.
        community_type: Type of community (study/coding/professional/casual/general).
        session_id: Unique session ID for maintaining conversation context.
        conversation_history: Optional list of {"role": ..., "content": ...} dicts.

    Returns:
        The AI-generated response string.
    """
    # Validate inputs
    community_type = validate_community_type(community_type)
    intent = detect_intent(user_message)

    # Build system prompt
    system_prompt = _build_system_prompt(community_type, intent)

    # Build contents list from conversation history
    contents = []
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", msg.get("parts", ""))
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)],
                )
            )

    # Add current user message
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    )

    # Generate response with retry logic for rate limits
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=1024,
                ),
            )
            return format_response(response.text)

        except Exception as api_err:
            last_error = api_err
            error_str = str(api_err)

            # Retry on rate limit (429) errors
            if "429" in error_str or "resource_exhausted" in error_str.lower():
                wait_time = RETRY_DELAY * (attempt + 1)
                if attempt < MAX_RETRIES - 1:
                    print(f"  [Rate limited, retrying in {wait_time}s... ({attempt + 1}/{MAX_RETRIES})]")
                    time.sleep(wait_time)
                    continue

            # Don't retry on other errors
            break

    # All retries failed — return user-friendly message
    error_msg = str(last_error)
    print(f"  [Gemini API error: {error_msg[:200]}]")

    if "429" in error_msg or "resource_exhausted" in error_msg.lower():
        return ("I'm currently rate-limited by the API. "
                "Please wait 30-60 seconds and try again.")
    if "api" in error_msg.lower() or "key" in error_msg.lower() or "invalid" in error_msg.lower():
        return "There seems to be a configuration issue. Please check the API key."
    return "Sorry, I encountered an issue while processing your message. Please try again."


def get_quick_reply(user_message: str, community_type: str = "general") -> str:
    """
    Stateless single-shot reply (no conversation memory).
    Useful for Discord messages where context isn't needed.
    """
    return generate_reply(user_message, community_type, session_id=None)
