import aiohttp
import json
import os
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_FILE = os.path.join(BASE_DIR, 'data/tokens.json')

def load_tokens():
    with open(TOKENS_FILE, 'r') as f:
        return json.load(f)

TOKENS = load_tokens()

async def get_user_id(username):
    url = 'https://api.twitch.tv/helix/users'
    headers = {
        'Authorization': f'Bearer {TOKENS["TWITCH_OAUTH_TOKEN"]}',
        'Client-Id': TOKENS["TWITCH_CLIENT_ID"],
    }
    params = {
        'login': username
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(data)
                if data['data']:
                    return data['data'][0]['id']
                else:
                    return None
            else:
                print(f'Failed to get user ID for {username}. Response: {resp.status} - {await resp.text()}')
                return None

# Add this part to run the asynchronous function
if __name__ == "__main__":
    username = 'kiziakixx'
    asyncio.run(get_user_id(username))
