# This file implements connection to Twitch's EventSub WebSockets API.
# The protocol is as follows:
# 1) After the connection, Twitch sends a welcome message with info, including session id.
# 2) We send a subscription request to a different API endpoint.
# 3) We receive notification message, keepalive message, ping message or reconnect message.
# If we recieve a notification message, process it.
# If we don't recieve a notification or a keepalive message within period indicated by welcome message, reconnect.
# If we recieve a ping message, send a pong message. Pings do not reset keepalive timer.
# websockets library takes care of ping-pong bullshit, so I don't have to keep track of it. Thank fuck.
# If we recieve a reconnect message, reconnect to URI provided in the message.
# There is also revocation message, but it is not relevant to this application because I am not revoking my own bot lol.

import asyncio
import json
import os
from typing import AsyncGenerator

import aiohttp
import websockets

import messages

debug = False
token = os.environ["TWITCH_BOT_ACCESS_TOKEN"]
client_id = os.environ["TWITCH_CLIENT_ID"]
headers = {
    "Authorization": f"Bearer {token}",
    "Client-Id": client_id,
    "Content-Type": "application/json",
}
subscriptions = [
    {
        "type": "channel.follow",
        "version": "2",
        "condition": {"broadcaster_user_id": "147239368", "moderator_user_id": "147239368"},
    },
    {
        "type": "channel.subscribe",
        "version": "1",
        "condition": {"broadcaster_user_id": "147239368"},
    },
    {
        "type": "channel.subscription.message",
        "version": "1",
        "condition": {"broadcaster_user_id": "147239368"},
    },
    {
        "type": "channel.subscription.gift",
        "version": "1",
        "condition": {"broadcaster_user_id": "147239368"},
    },
    {
        "type": "channel.cheer",
        "version": "1",
        "condition": {"broadcaster_user_id": "147239368"},
    },
    {
        "type": "channel.raid",
        "version": "1",
        "condition": {"to_broadcaster_user_id": "147239368"},
    },
]
tiers = {
    "1000": "Tier 1",
    "2000": "Tier 2",
    "3000": "Tier 3",
    "Prime": "Prime",
}


async def send(session: aiohttp.ClientSession, url: str, session_id: str, data: dict):
    data.update({"transport": {"method": "websocket", "session_id": session_id}})
    await asyncio.sleep(0.1)  # Don't want to spam Twitch's servers.
    async with session.post(url, json=data) as resp:
        r_json = await resp.json()
        print(r_json)
        return r_json


async def subscribe(subs: list[dict], session_id: str):
    async with aiohttp.ClientSession(headers=headers) as session:
        await asyncio.gather(
            *[send(
                session,
                "https://api.twitch.tv/helix/eventsub/subscriptions",
                session_id=session_id,
                data=subscription,
            )
                for subscription in subs]
        )


async def message_gen() -> AsyncGenerator[dict, None]:
    uri = "ws://localhost:8080/eventsub" if debug else "wss://eventsub-beta.wss.twitch.tv/ws"
    while True:
        async with websockets.connect(uri, ping_interval=None) as socket:
            welcome_message = await socket.recv()
            welcome_data = json.loads(welcome_message)
            assert welcome_data["metadata"]["message_type"] == "session_welcome"
            session_id = welcome_data["payload"]["session"]["id"]
            keepalive_timeout = welcome_data["payload"]["session"][
                "keepalive_timeout_seconds"
            ]
            await subscribe(subscriptions, session_id)
            yield welcome_data
            while True:
                try:
                    message = await asyncio.wait_for(
                        socket.recv(), int(keepalive_timeout) * 1.5
                    )
                except asyncio.TimeoutError:
                    print("Timeout. Reconnecting.")
                    break
                message_data = json.loads(message)
                message_type = message_data["metadata"]["message_type"]
                match message_type:
                    case "session_keepalive":
                        # Twitch sends keepalive messages to inform us that they are still there,
                        # we just have no notifications at the moment.
                        # We don't need to do anything with these messages.
                        pass
                    case "notification":
                        yield message_data  # That's what we are here for.
                    case "session_reconnect":
                        uri = message_data["payload"]["session"]["reconnect_url"]
                        print(f"Reconnecting to {uri}")
                        break  # Welcome to Bodgeland, population: me.
                    case _:
                        print(message)


class MessageProcessor:
    def __init__(self, generator: AsyncGenerator[dict, None]):
        self.generator = generator
        self.discord = None
        self.twitch = None
        self.followers = None

    async def run(self):
        async for message in self.generator:
            await self.process(message)

    async def process(self, message: dict):
        message_type = message["metadata"]["message_type"]
        if message_type == "notification":
            await self.process_notification(message)
        else:
            pass

    async def process_notification(self, message: dict):
        event_type = message["payload"]["subscription"]["type"]
        twitch_bot = self.twitch
        match event_type:
            case "channel.follow":
                if message["payload"]["event"]["user_id"] in self.followers:
                    return
                self.followers.add(message["payload"]["event"]["user_id"])
                username = message["payload"]["event"]["user_name"]
                response = messages.follow_message.format(user=username)
            case "channel.subscription":
                if message["payload"]["event"]["is_gift"]:
                    return
                tier = tiers[message["payload"]["event"]["tier"]]
                username = message["payload"]["event"]["user_name"]
                response = messages.subscription_message.format(tier=tier, user=username)
            case "channel.subscription.message":
                if message["payload"]["event"]["is_gift"]:
                    return
                tier = tiers[message["payload"]["event"]["tier"]]
                username = message["payload"]["event"]["user_name"]
                streak = message["payload"]["event"]["cumulative_months"]
                if streak == 1 or streak is None:
                    return
                response = messages.resubscription_message.format(tier=tier, months=streak, user=username)
            case "channel.subscription.gift":
                tier = tiers[message["payload"]["event"]["tier"]]
                count = message["payload"]["event"]["total"]
                sender = message["payload"]["event"]["user_name"]
                total = message["payload"]["event"]["cumulative_total"]
                if message["payload"]["event"]["is_anonymous"] and count == 1:
                    response = messages.anon_gift_message.format(tier=tier)
                elif message["payload"]["event"]["is_anonymous"]:
                    response = messages.anon_gifts_message.format(tier=tier, count=count)
                elif count == 1:
                    response = messages.gift_message.format(tier=tier, user=sender, total=total)
                else:
                    response = messages.gifts_message.format(tier=tier, count=count, user=sender, total=total)
            case "channel.cheer":
                bits = message["payload"]["event"]["bits"]
                username = message["payload"]["event"]["user_name"]
                if message["payload"]["event"]["is_anonymous"]:
                    response = messages.anon_cheer_message.format(bits=bits)
                else:
                    response = messages.cheer_message.format(bits=bits, user=username)
            case "channel.raid":
                username = message["payload"]["event"]["from_broadcaster_user_name"]
                viewers = message["payload"]["event"]["viewers"]
                response = messages.raid_message.format(user=username, viewers=viewers)
            case _:
                response = "But nobody came."  # This is never reached, but type checker will complain if it's not here.
        await twitch_bot.boss.send(response)


async def setup():
    generator = message_gen()
    await anext(generator)  # Wait for welcome message and send subscription requests.
    processor = MessageProcessor(generator)
    return processor
