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
import get_token

import sys


async def main():
    discord_client, twitch_client, eventsub_processor = await asyncio.gather(
        discord_bot.setup(),
        twitch_bot.setup(),
        eventsub.setup(),
    )
    # discord_client, twitch_client = await asyncio.gather(
    #     discord_bot.setup(), twitch_bot.setup()
    # )
    print("Setup complete.")
    # Give bots a reference to each other, so they can communicate. (I don't know if this is a good idea)
    discord_client.twitch = twitch_client
    twitch_client.discord = discord_client
    # Give the eventsub processor a reference to the twitch client, so it can communicate.
    eventsub_processor.twitch = twitch_client
    # Give the eventsub processor a reference to the discord client, so it can communicate.
    eventsub_processor.discord = discord_client
    # Give the eventsub processor a list of followers to avoid unfollow-follow spam.
    # But first, need to ensure that Twitch bot has connected to the Twitch API.
    await asyncio.sleep(5)  # Bodgeland, my hometown.
    eventsub_processor.followers = {event.from_user.id for event in await twitch_client.boss_user.fetch_followers()}
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
