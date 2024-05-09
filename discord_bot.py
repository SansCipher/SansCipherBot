import asyncio

import discord
from discord import app_commands

import config

# Get the bot token from the tokens.json.
token, guild = config.get_tokens(["DISCORD_TOKEN", "DISCORD_GUILD"])
guild = int(guild)


def is_me():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 195227710883233792

    return app_commands.check(predicate)


@app_commands.command(name="ping", description="Pong!")
@is_me()
async def ping(interaction: discord.Interaction):
    print(interaction)
    await interaction.response.send_message("Pong!")


commands = [ping]


class SansCipherBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
        self.twitch = None  # Reference to the twitch bot.
        self.guild = None  # Reference to the guild.

    async def on_ready(self):
        self.guild = self.get_guild(guild)
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        for command in commands:
            self.tree.add_command(command)

        @self.tree.command(name="eval", description="Evaluate Python code.")
        @is_me()
        async def eval_command(interaction: discord.Interaction, code: str):
            try:
                loc = locals().copy()
                loc["self"] = self
                answer = eval(code, globals(), loc)
                if asyncio.iscoroutine(answer):
                    answer = await answer
            except Exception as e:
                answer = e
            await interaction.response.send_message(str(answer))

        await self.tree.sync()
        print("Synced application commands.")
        print("------")


async def setup():
    bot = SansCipherBot()
    print("Starting Discord bot...")
    asyncio.create_task(bot.start(token))
    return bot


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(setup())
    loop.run_forever()
