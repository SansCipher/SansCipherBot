import asyncio
import json

import discord
from discord import app_commands

import config

# Get the bot token from the tokens.json.
token, guild = config.get_tokens(["DISCORD_TOKEN", "DISCORD_GUILD"])
guild = int(guild)

with open("botc_characters.json", encoding="utf-8-sig") as f:
    characters = json.load(f)


def is_me():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 195227710883233792

    return app_commands.check(predicate)


@app_commands.command(name="ping", description="Pong!")
@is_me()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


commands = [ping]


async def _exit(bot):
    if bot.twitch:
        await bot.twitch.close()
    await bot.close()
    await asyncio.get_event_loop().stop()


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

        @self.tree.command(
            name="exit", description="Exit the bot and stop the program."
        )
        @is_me()
        async def exit_command(interaction: discord.Interaction):
            await interaction.response.send_message("Exiting the bot...")
            await _exit(self)

        @self.tree.command(
            name="character", description="Look up a Blood on the Clocktower character."
        )
        async def character_command(interaction: discord.Interaction, name: str):
            name = name.lower()
            if name not in characters:
                await interaction.response.send_message(f"Character {name} not found.")
            else:
                character = characters[name]
                await interaction.response.send_message(character)

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
