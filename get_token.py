# This is an auxiliary script, it's goal is to fetch the token from the Twitch API.
# We use authorization code grant flow, redirecting to localhost.

import os
import webbrowser
import re
import asyncio
import aiohttp
import secrets

import config

client_id, client_secret = config.get_tokens(
    ["TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET"]
)
redirect_uri = "https://localhost"
scopes = [
    "bits:read",
    "channel:edit:commercial",
    "channel:manage:broadcast",
    "channel:manage:polls",
    "channel:manage:predictions",
    "channel:manage:raids",
    "channel:manage:redemptions",
    "channel:manage:vips",
    "channel:read:subscriptions",
    "channel:read:redemptions",
    "moderator:read:followers",
    "moderator:manage:shoutouts",
    "chat:edit",
    "chat:read",
]

state = secrets.token_urlsafe(16)
url = (
    "https://id.twitch.tv/oauth2/authorize"
    f"?client_id={client_id}"
    f"&redirect_uri={redirect_uri}"
    f"&response_type=code"
    f"&scope={' '.join(scopes)}"
    f"&state={state}"
)


async def get_token(code: str):
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        r = await session.post("https://id.twitch.tv/oauth2/token", data=data)
        data = await r.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        print(f"Access token: {access_token}, refresh token: {refresh_token}")
        config.set_tokens(
            {
                "TWITCH_BOT_ACCESS_TOKEN": access_token,
                "TWITCH_BOT_REFRESH_TOKEN": refresh_token,
            }
        )


async def amain():
    webbrowser.open(url)
    print("Enter the redirect URL:")
    redirect = input()
    code, check_state = re.search(r"code=(.*)&scope=.*&state=(.*)", redirect).groups()
    assert check_state == state
    await get_token(code)


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
