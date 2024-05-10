# This application will be running two bots, Discord and Twitch.
# Both bots will be able to interact with each other.
# Discord bot will use discord.py
# Twitch bot will use twitchio
# In order to make this program easier to maintain, I will split the code into multiple files.
# The main.py file will be used to run the program.
# The discord_bot.py file will be used to run the discord bot.
# The twitch_bot.py file will be used to run the twitch bot.
# The configuration variables will be stored in environment variables (for security reasons).

import asyncio
import discord_bot
import twitch_bot
import eventsub
import config
import get_token

import sys


async def main():
    discord_client = await discord_bot.setup()
    twitch_client = await twitch_bot.setup()
    eventsub_processor = await eventsub.setup()
    print("Setup complete.")
    discord_client.twitch = twitch_client
    twitch_client.discord = discord_client
    eventsub_processor.twitch = twitch_client
    eventsub_processor.discord = discord_client
    # Give the eventsub processor a list of followers to avoid unfollow-follow spam.
    # But first, need to ensure that Twitch bot has connected to the Twitch API.
    await asyncio.sleep(5)  # Bodgeland, my hometown.
    twitch_token = config.get_tokens(["TWITCH_BOT_ACCESS_TOKEN"])[0]
    eventsub_processor.followers = {
        event.user.id
        for event in await twitch_client.boss_user.fetch_channel_followers(twitch_token)
    }
    asyncio.create_task(eventsub_processor.run())


def start():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg in ("-t", "--token"):
        get_token.main()
    else:
        start()
