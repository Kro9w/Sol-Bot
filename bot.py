import os
import re
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# Embed descriptions are capped at 4096 characters by Discord. Keep a little
# headroom below that limit.
ECHO_MAX_LENGTH = 4000
SOL_COLOUR = discord.Colour(0xF5B301)
NO_MENTIONS = discord.AllowedMentions.none()

# A raw channel ID (17-20 digits) or a channel mention such as <#123456789012345678>.
CHANNEL_REF_PATTERN = re.compile(r"^(?:<#(\d{17,20})>|(\d{17,20}))$")
ECHO_TARGET_TYPES = (
    discord.TextChannel,
    discord.Thread,
    discord.VoiceChannel,
    discord.StageChannel,
)


class SolBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=".",
            intents=intents,
        )

    async def setup_hook(self) -> None:
        if not GUILD_ID:
            raise RuntimeError("GUILD_ID is missing from .env")

        try:
            guild_id = int(GUILD_ID)
        except ValueError as exc:
            raise RuntimeError(
                "GUILD_ID in .env must be a numeric Discord server ID"
            ) from exc

        guild = discord.Object(id=guild_id)

        # Sync slash commands to your server.
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print(f"Slash commands synced to server {guild_id}.")

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("☀️ Sol Bot is online!")

        print(
            "Registered prefix commands:",
            [command.name for command in self.commands],
        )

    async def on_message(self, message: discord.Message) -> None:
        # Ignore messages sent by bots.
        if message.author.bot:
            return

        # Process commands such as .hello.
        await self.process_commands(message)

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        if isinstance(error, commands.CommandNotFound):
            return

        print(
            f"Prefix command error: "
            f"{type(error).__name__}: {error}"
        )

        await ctx.send(
            "Sorry, that command ran into an error."
        )

    async def close(self) -> None:
        print("Sol Bot is shutting down.")
        await super().close()


def validate_echo_message(message: str) -> Optional[str]:
    """Return a user-facing error if the message can't be echoed, else None."""
    if not message.strip():
        return (
            "There's nothing to echo! Try `/echo message: Hello, world!` "
            "or `.echo Hello, world!`"
        )

    if len(message) > ECHO_MAX_LENGTH:
        return (
            f"That message is too long to echo ({len(message):,} characters). "
            f"Please keep it to {ECHO_MAX_LENGTH:,} characters or fewer."
        )

    return None


def build_echo_embed(
    message: str,
    requester: discord.abc.User,
) -> discord.Embed:
    """Build the embed used by both the slash and prefix echo commands."""
    embed = discord.Embed(
        description=message,
        colour=SOL_COLOUR,
    )
    embed.set_footer(
        text=f"☀️ Sol Bot • Requested by {requester.display_name}"
    )
    return embed


def parse_channel_id(raw: str) -> Optional[int]:
    """Extract a channel ID from a raw ID or a <#id> mention."""
    match = CHANNEL_REF_PATTERN.match(raw.strip())
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def can_send_embeds(
    channel: Union[discord.abc.GuildChannel, discord.Thread],
    member: discord.Member,
) -> bool:
    """Check whether a member can see a channel and send embeds in it."""
    try:
        perms = channel.permissions_for(member)
    except discord.ClientException:
        return False

    # Threads use their own send permission.
    if isinstance(channel, discord.Thread):
        can_send = perms.send_messages_in_threads
    else:
        can_send = perms.send_messages

    return perms.view_channel and can_send and perms.embed_links


def resolve_echo_target(
    guild: Optional[discord.Guild],
    member: discord.abc.User,
    raw_channel: str,
) -> tuple[Optional[discord.abc.Messageable], Optional[str]]:
    """Resolve a channel ID for echoing.

    Returns (channel, None) on success or (None, error message) on failure.
    The requester must be allowed to see and post embeds in the target
    channel themselves, so echo can't be used to get around channel
    permissions.
    """
    if guild is None or not isinstance(member, discord.Member):
        return None, "Echoing to another channel only works inside a server."

    channel_id = parse_channel_id(raw_channel)
    if channel_id is None:
        return None, (
            "That doesn't look like a valid channel ID. Turn on Developer "
            "Mode, then right-click a channel and choose **Copy Channel ID**."
        )

    # Only channels in this server can be targeted. Unknown channels and
    # channels the requester can't see get the same message so this can't
    # be used to discover hidden channels.
    channel = guild.get_channel_or_thread(channel_id)
    not_found = (
        "I couldn't find that channel in this server, "
        "or you don't have access to it."
    )
    if not isinstance(channel, ECHO_TARGET_TYPES):
        return None, not_found

    try:
        if not channel.permissions_for(member).view_channel:
            return None, not_found
    except discord.ClientException:
        return None, not_found

    if not can_send_embeds(channel, member):
        return None, (
            f"You don't have permission to send messages and embeds "
            f"in {channel.mention}."
        )

    if not can_send_embeds(channel, guild.me):
        return None, (
            f"I don't have permission to send messages and embeds "
            f"in {channel.mention}."
        )

    return channel, None


bot = SolBot()

@bot.tree.command(
    name="hello",
    description="Say hello to Sol Bot!",
)
async def hello_slash(
    interaction: discord.Interaction,
) -> None:
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}! ☀️ "
        "Welcome to The Solari Initiative."
    )


@bot.command(
    name="hello",
    help="Say hello to Sol Bot.",
)
async def hello_prefix(
    ctx: commands.Context,
) -> None:
    await ctx.send(
        f"Hello, {ctx.author.mention}! ☀️ "
        "Welcome to The Solari Initiative."
    )

@bot.tree.command(
    name="tanginamo",
    description="Trip lang",
)
async def tanginamo_slash(
    interaction: discord.Interaction,
) -> None:
    await interaction.response.send_message(
        f"Putanginamo rin gago {interaction.user.mention}!"
    )


@bot.tree.command(
    name="echo",
    description="Make Sol Bot repeat a message.",
)
@app_commands.describe(
    message="The message for Sol Bot to repeat",
    channel_id="Optional: the ID of a channel in this server to send it to",
)
async def echo_slash(
    interaction: discord.Interaction,
    message: str,
    channel_id: Optional[str] = None,
) -> None:
    error = validate_echo_message(message)
    if error:
        await interaction.response.send_message(error, ephemeral=True)
        return

    target = None
    if channel_id and channel_id.strip():
        target, error = resolve_echo_target(
            interaction.guild,
            interaction.user,
            channel_id,
        )
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

    embed = build_echo_embed(message, interaction.user)

    # No target, or the target is the current channel: reply here as usual.
    if target is None or target.id == interaction.channel_id:
        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=NO_MENTIONS,
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        sent = await target.send(embed=embed, allowed_mentions=NO_MENTIONS)
    except discord.HTTPException as exc:
        print(f"Echo to channel {target.id} failed: {type(exc).__name__}")
        await interaction.followup.send(
            f"I couldn't send that to {target.mention}.",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        f"Sent to {target.mention}: {sent.jump_url}",
        ephemeral=True,
    )


@bot.command(
    name="echo",
    help=(
        "Make Sol Bot repeat a message. "
        "Start with a channel ID to send it to another channel."
    ),
)
async def echo_prefix(
    ctx: commands.Context,
    *,
    message: str = "",
) -> None:
    # `.echo <channel id> <message>` targets another channel. A leading ID is
    # only treated as a channel when message text follows it.
    target = None
    parts = message.split(None, 1)
    if len(parts) == 2 and parse_channel_id(parts[0]) is not None:
        target, error = resolve_echo_target(ctx.guild, ctx.author, parts[0])
        if error:
            await ctx.send(error, allowed_mentions=NO_MENTIONS)
            return
        message = parts[1]

    error = validate_echo_message(message)
    if error:
        await ctx.send(error, allowed_mentions=NO_MENTIONS)
        return

    embed = build_echo_embed(message, ctx.author)

    if target is None or target.id == ctx.channel.id:
        await ctx.send(embed=embed, allowed_mentions=NO_MENTIONS)
        return

    try:
        await target.send(embed=embed, allowed_mentions=NO_MENTIONS)
    except discord.HTTPException as exc:
        print(f"Echo to channel {target.id} failed: {type(exc).__name__}")
        await ctx.send(
            f"I couldn't send that to {target.mention}.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    await ctx.send(
        f"Sent to {target.mention}.",
        allowed_mentions=NO_MENTIONS,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is missing from .env"
        )

    bot.run(TOKEN)