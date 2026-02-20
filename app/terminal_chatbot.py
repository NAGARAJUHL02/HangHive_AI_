"""
HANG — Terminal Chatbot
Interactive terminal interface for testing the chatbot locally.
Run: py app/terminal_chatbot.py
"""

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils import COMMUNITY_TYPES, validate_community_type
from app.chatbot import generate_reply
from app.automod import check_message


# ---------------------------------------------------------------------------
# Terminal UI
# ---------------------------------------------------------------------------

BANNER = """
╔══════════════════════════════════════════════════════╗
║                    🟢  HANG — Terminal               ║
║          Your smart community assistant              ║
╚══════════════════════════════════════════════════════╝
"""

def select_community_type() -> str:
    """Let the user select a community type at startup."""
    print("\nAvailable community types:")
    for i, ct in enumerate(COMMUNITY_TYPES, 1):
        labels = {
            "study": "Study — Academic & educational help",
            "coding": "Coding — Programming & technical help",
            "professional": "Professional — Formal & office discussions",
            "casual": "Casual — Friendly & relaxed conversations",
            "general": "General — All-purpose help",
        }
        print(f"  {i}. {labels.get(ct, ct)}")

    while True:
        choice = input("\nSelect community type (1-5) or type name: ").strip()

        # Number selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(COMMUNITY_TYPES):
                selected = COMMUNITY_TYPES[idx]
                print(f"\n✓ Community type set to: {selected}")
                return selected
            else:
                print("  Invalid number. Please enter 1-5.")
                continue

        # Name selection
        validated = validate_community_type(choice)
        if validated == choice.lower():
            print(f"\n✓ Community type set to: {validated}")
            return validated
        else:
            print(f"  '{choice}' is not valid. Defaulting to 'general'.")
            return "general"


def main():
    """Main terminal chatbot loop."""
    print(BANNER)

    community_type = select_community_type()
    conversation_history = []

    print(f"\nYou can now chat with HANG ({community_type} mode).")
    print("Type 'quit' or 'exit' to stop.\n")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n📝 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nGoodbye! 👋")
            break

        # Command handling
        if user_input.startswith("/"):
            handle_command(user_input, community_type)
            continue

        # Auto-moderation check
        is_safe, reason = check_message(user_input)
        if not is_safe:
            print(f"\n⚠️  AutoMod: {reason}")
            print("   Your message was flagged and not sent to the AI.")
            continue

        # Generate AI reply
        print("\n🤖 HANG: Thinking...")

        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_input,
        })

        reply = generate_reply(
            user_message=user_input,
            community_type=community_type,
            session_id="terminal",
            conversation_history=conversation_history,
        )

        # Add AI reply to history
        conversation_history.append({
            "role": "model",
            "content": reply,
        })

        # Clear "Thinking..." and print response
        print(f"\033[A\033[K🤖 HANG: {reply}")


def handle_command(command: str, community_type: str):
    """Handle slash commands in terminal mode."""
    cmd = command.lower().strip()

    if cmd == "/help":
        print("\n📋 Available commands:")
        print("  /help        — Show this help menu")
        print("  /community   — Show current community type")
        print("  /clear       — Clear conversation history")
        print("  /quit        — Exit the chatbot")

    elif cmd == "/community":
        print(f"\n📌 Current community type: {community_type}")

    elif cmd == "/clear":
        print("\n🗑️  Conversation history cleared.")

    elif cmd in ("/quit", "/exit"):
        print("\nGoodbye! 👋")
        sys.exit(0)

    else:
        print(f"\n❓ Unknown command: {command}")
        print("   Type /help to see available commands.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
