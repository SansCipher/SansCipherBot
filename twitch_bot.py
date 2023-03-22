# import re
import os
import asyncio

import twitchio
import aiohttp

# Get the bot tokens from the environment variables.
bot_access_token = os.environ["TWITCH_BOT_ACCESS_TOKEN"]
bot_refresh_token = os.environ["TWITCH_BOT_REFRESH_TOKEN"]
client_id = os.environ["TWITCH_CLIENT_ID"]
client_secret = os.environ["TWITCH_CLIENT_SECRET"]


async def refresh():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": bot_refresh_token,
            },
        ) as resp:
            data = await resp.json()
            print(data)
            global bot_access_token
            bot_access_token = data["access_token"]
            os.environ["TWITCH_ACCESS_TOKEN"] = bot_access_token


async def validate():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://id.twitch.tv/oauth2/validate",
            headers={"Authorization": f"OAuth {bot_access_token}"},
        ) as resp:
            if resp.status == 401:
                await refresh()
            else:
                print("Twitch access token is valid.")
                return True


class SansCipherBot(twitchio.Client):
    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__(bot_access_token, initial_channels=["sanscipher"])
        self.boss: twitchio.Channel = None  # Reference to the sanscipher channel.
        self.boss_user: twitchio.User = None  # Reference to the sanscipher user.
        self.discord = None  # Reference to the discord bot.

    async def event_ready(self):
        self.boss = self.get_channel("sanscipher")
        self.boss_user = (await self.fetch_users(["sanscipher"]))[0]
        print(f"Logged in as {self.nick} (ID: {self.user_id})")
        print(f"Boss: {self.boss}")
        print("------")

    async def event_token_expired(self):
        await refresh()
        return bot_access_token


async def setup():
    await validate()
    bot = SansCipherBot()
    asyncio.create_task(bot.start())
    return bot
