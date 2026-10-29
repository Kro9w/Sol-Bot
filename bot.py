import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


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

        # TEMPORARY DIAGNOSTIC LOGGING.
        # Remove this block after troubleshooting.
        print(
            f"MESSAGE RECEIVED | "
            f"Author: {message.author} | "
            f"Content: {message.content!r}"
        )

        if message.content.startswith("."):
            print("DOT COMMAND DETECTED")

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

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is missing from .env"
        )

    bot.run(TOKEN)