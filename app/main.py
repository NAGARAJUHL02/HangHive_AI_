"""
HANG — Discord Bot (main.py)
Discord bot entry point with AI chat, auto-moderation, and moderation commands.
Run: py app/main.py
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import discord
from discord.ext import commands
from discord import app_commands

from app.utils import DISCORD_BOT_TOKEN, validate_community_type
from app.chatbot import generate_reply
from app.automod import check_message, censor_message, get_violation_level
from app.moderation import warn_user, mute_user, kick_user, ban_user, get_mod_log, get_warnings
from app.summarizer import summarize_messages


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = False  # Set to True after enabling Message Content Intent in Discord Developer Portal

bot = commands.Bot(command_prefix="!", intents=intents)

# Per-channel community type settings (can be configured per server)
_channel_community_types = {}

# Message buffer for summarization (per channel, last 50 messages)
_message_buffer = {}
_BUFFER_SIZE = 50


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    """Called when the bot is connected and ready."""
    print(f"{'='*50}")
    print(f"  HANG is online!")
    print(f"  Logged in as: {bot.user.name} ({bot.user.id})")
    print(f"  Servers: {len(bot.guilds)}")
    print(f"{'='*50}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over HangHive | /ask"
        )
    )

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"  Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"  Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Process every message for auto-moderation."""
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Ignore DMs
    if not message.guild:
        return

    # Buffer messages for summarization
    channel_id = str(message.channel.id)
    if channel_id not in _message_buffer:
        _message_buffer[channel_id] = []
    _message_buffer[channel_id].append({
        "author": message.author.display_name,
        "content": message.content,
    })
    # Keep only last N messages
    _message_buffer[channel_id] = _message_buffer[channel_id][-_BUFFER_SIZE:]

    # Auto-moderation check
    is_safe, reason = check_message(message.content)
    if not is_safe:
        level = get_violation_level(reason)
        try:
            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention} — {reason}",
                delete_after=10
            )
            if level == "high":
                # Auto-warn for high severity
                warn_user(
                    str(message.author.id),
                    message.author.display_name,
                    reason,
                    "AutoMod"
                )
        except discord.Forbidden:
            pass  # Missing permissions
        return

    # Process bot commands
    await bot.process_commands(message)


# ---------------------------------------------------------------------------
# Slash Commands — AI Chat
# ---------------------------------------------------------------------------

@bot.tree.command(name="ask", description="Ask HANG a question")
@app_commands.describe(question="Your question for HANG")
async def ask(interaction: discord.Interaction, question: str):
    """Ask HANG a question."""
    await interaction.response.defer(thinking=True)

    channel_id = str(interaction.channel_id)
    community_type = _channel_community_types.get(channel_id, "general")

    reply = await asyncio.to_thread(
        generate_reply,
        user_message=question,
        community_type=community_type,
        session_id=channel_id,
    )

    # Truncate if too long for Discord (2000 char limit)
    if len(reply) > 1900:
        reply = reply[:1900] + "\n\n*...response truncated*"

    embed = discord.Embed(
        description=reply,
        color=discord.Color.blue()
    )
    embed.set_author(name="HANG", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text=f"Asked by {interaction.user.display_name}")

    await interaction.followup.send(embed=embed)


# ---------------------------------------------------------------------------
# Slash Commands — Community Type
# ---------------------------------------------------------------------------

@bot.tree.command(name="setcommunity", description="Set the community type for this channel")
@app_commands.describe(community_type="Community type: study, coding, professional, casual, general")
@app_commands.checks.has_permissions(manage_channels=True)
async def setcommunity(interaction: discord.Interaction, community_type: str):
    """Set the community type for the channel."""
    validated = validate_community_type(community_type)
    channel_id = str(interaction.channel_id)
    _channel_community_types[channel_id] = validated

    await interaction.response.send_message(
        f"✅ Community type for this channel set to **{validated}**.",
        ephemeral=True
    )


# ---------------------------------------------------------------------------
# Slash Commands — Summarization
# ---------------------------------------------------------------------------

@bot.tree.command(name="summarize", description="Summarize recent messages in this channel")
@app_commands.describe(count="Number of recent messages to summarize (default: 20)")
async def summarize(interaction: discord.Interaction, count: int = 20):
    """Summarize recent channel messages."""
    await interaction.response.defer(thinking=True)

    channel_id = str(interaction.channel_id)
    messages = _message_buffer.get(channel_id, [])

    if not messages:
        await interaction.followup.send("No messages to summarize in this channel.")
        return

    # Take the requested number of messages
    to_summarize = messages[-min(count, len(messages)):]

    summary = await asyncio.to_thread(summarize_messages, to_summarize)

    embed = discord.Embed(
        title="📋 Channel Summary",
        description=summary,
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Summarized {len(to_summarize)} messages")

    await interaction.followup.send(embed=embed)


# ---------------------------------------------------------------------------
# Slash Commands — Moderation
# ---------------------------------------------------------------------------

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user to warn", reason="Reason for warning")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    """Warn a user."""
    result = warn_user(
        str(user.id), user.display_name, reason, interaction.user.display_name
    )

    embed = discord.Embed(
        title="⚠️ User Warned",
        description=result["message"],
        color=discord.Color.yellow()
    )
    log = get_mod_log("warn", interaction.user.display_name, user.display_name, reason)

    await interaction.response.send_message(embed=embed)
    print(log)


@bot.tree.command(name="mute", description="Mute/timeout a user")
@app_commands.describe(user="The user to mute", duration="Duration in minutes", reason="Reason for mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute_cmd(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str):
    """Mute a user using Discord timeout."""
    result = mute_user(user.display_name, duration, reason, interaction.user.display_name)

    try:
        await user.timeout(result["duration_timedelta"], reason=reason)

        embed = discord.Embed(
            title="🔇 User Muted",
            description=result["message"],
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to timeout this user.", ephemeral=True
        )


@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    """Kick a user from the server."""
    result = kick_user(user.display_name, reason, interaction.user.display_name)

    try:
        await user.kick(reason=reason)

        embed = discord.Embed(
            title="👢 User Kicked",
            description=result["message"],
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to kick this user.", ephemeral=True
        )


@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user to ban", reason="Reason for ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_cmd(interaction: discord.Interaction, user: discord.Member, reason: str):
    """Ban a user from the server."""
    result = ban_user(user.display_name, reason, interaction.user.display_name)

    try:
        await user.ban(reason=reason)

        embed = discord.Embed(
            title="🔨 User Banned",
            description=result["message"],
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to ban this user.", ephemeral=True
        )


@bot.tree.command(name="warnings", description="View warnings for a user")
@app_commands.describe(user="The user to check warnings for")
@app_commands.checks.has_permissions(moderate_members=True)
async def warnings_cmd(interaction: discord.Interaction, user: discord.Member):
    """View warnings for a user."""
    warns = get_warnings(str(user.id))

    if not warns:
        await interaction.response.send_message(
            f"✅ {user.display_name} has no warnings.", ephemeral=True
        )
        return

    lines = []
    for i, w in enumerate(warns, 1):
        lines.append(f"**{i}.** {w['reason']} — by {w['moderator']} ({w['timestamp'][:10]})")

    embed = discord.Embed(
        title=f"⚠️ Warnings for {user.display_name}",
        description="\n".join(lines),
        color=discord.Color.yellow()
    )
    embed.set_footer(text=f"Total: {len(warns)} warning(s)")

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    """Handle slash command errors."""
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ An error occurred. Please try again.", ephemeral=True
        )
        print(f"Command error: {error}")


# ---------------------------------------------------------------------------
# Run the bot
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "your_discord_bot_token_here":
        print("=" * 50)
        print("  ERROR: Discord bot token not set!")
        print("  Please add your token to the .env file:")
        print("  DISCORD_BOT_TOKEN=your_token_here")
        print("=" * 50)
        sys.exit(1)

    print("Starting HANG Discord bot...")
    bot.run(DISCORD_BOT_TOKEN)
