import asyncio
import logging
import os
import json
import random
import time
import aiohttp
from twitchio.ext import commands
import simpleobsws

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(BASE_DIR, 'bot.log')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

console_formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

TOKENS_FILE = os.path.join(BASE_DIR, 'tokens.json')
def load_tokens():
    with open(TOKENS_FILE, 'r') as f:
        return json.load(f)

TOKENS = load_tokens()
TWITCH_CLIENT_ID = TOKENS['TWITCH_CLIENT_ID']
TWITCH_OAUTH_TOKEN = TOKENS['TWITCH_OAUTH_TOKEN']
GIVEAWAY_FILE = os.path.join(BASE_DIR, 'giveaway.json')
CHANNEL_NAME = 'urxi_'
BROADCASTER_ID = "1034744882"

parameters = simpleobsws.IdentificationParameters()
parameters.eventSubscriptions = (1 << 0) | (1 << 2)
ws = simpleobsws.WebSocketClient(url='ws://localhost:4444', password='risBs8nGQX38EpEh', identification_parameters=parameters)

async def get_scene_item_id(scene_name, source_name):
    response = await ws.call(simpleobsws.Request('GetSceneItemList', {'sceneName': scene_name}))
    if response.ok():
        for item in response.responseData['sceneItems']:
            if item['sourceName'] == source_name:
                return item['sceneItemId']
    print(f"Source '{source_name}' not found in scene '{scene_name}'.")
    return None

async def toggle_source_visibility(scene_name, source_name, duration=10):
    scene_item_id = await get_scene_item_id(scene_name, source_name)
    if not scene_item_id:
        return

    # Show the source
    await ws.call(simpleobsws.Request('SetSceneItemEnabled', {
        'sceneName': scene_name,
        'sceneItemId': scene_item_id,
        'sceneItemEnabled': True
    }))
    print(f'Source {source_name} is now visible in {scene_name} for {duration} seconds.')

    await asyncio.sleep(duration)

    # Hide the source
    await ws.call(simpleobsws.Request('SetSceneItemEnabled', {
        'sceneName': scene_name,
        'sceneItemId': scene_item_id,
        'sceneItemEnabled': False
    }))
    print(f'Source {source_name} is now hidden in {scene_name}.')

async def toggleobs(scene_name,source_name):
    if not ws or not ws.identified:
        print("OBS WebSocket is not connected or identified. Skipping OBS toggle.")
        return  # Skip the OBS functionality if not connected

    await toggle_source_visibility(scene_name, source_name, 20)
    print(f"Toggled visibility of {source_name} in OBS.")

def load_giveaway_entries():
    """Load giveaway entries from a file. If the file does not exist, start with an empty list."""
    if os.path.exists(GIVEAWAY_FILE):
        with open(GIVEAWAY_FILE, 'r') as f:
            try:
                return json.load(f)
            except (ValueError, json.JSONDecodeError):
                return []
    return []

async def update_winner_file(winner_name):
    """Write the winner's name to a file."""
    winner_file_path = os.path.join(BASE_DIR, 'winner.json')
    with open(winner_file_path, 'w') as f:
        json.dump(winner_name, f)

async def is_subscriber(user_id):
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {TWITCH_OAUTH_TOKEN}'
    }
    params = {
        'broadcaster_id': BROADCASTER_ID,
        'user_id': user_id
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://api.twitch.tv/helix/subscriptions', headers=headers, params=params) as response:
                if response.status == 200:
                    subscriptions_data = await response.json()

                    if len(subscriptions_data.get('data', [])) > 0:
                        logger.info(f"User {user_id} is subscribed.")
                        return True
                    else:
                        logger.info(f"User {user_id} is not subscribed.")
                        return False
                else:
                    logger.error(f"Failed to check subscription status: {response.status} {response.reason}")
                    return False
        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            return False

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(
            token=TWITCH_OAUTH_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick='kiziakixx',
            prefix='!',
            initial_channels=[CHANNEL_NAME]
        )
        self.giveaway_entries = load_giveaway_entries()

    def save_giveaway_entries(self):
        """Save the current giveaway entries to a file."""
        with open(GIVEAWAY_FILE, 'w') as f:
            json.dump(self.giveaway_entries, f)

    async def event_ready(self):
        logger.info(f'Logged in as {self.nick}')
        logger.info(f'Connected to {CHANNEL_NAME}')

    async def event_message(self, message):
        try:
            if message.author:
                logger.info(f'{message.author.name}: {message.content}')
                command = message.content.lstrip('!').lower()

                if command.startswith('สุ่ม'):
                    user_name = message.author.name
                    user_id = message.author.id
                    if user_name not in self.giveaway_entries:
                        is_sub = await is_subscriber(user_id)
                        if is_sub:
                            self.giveaway_entries.extend([user_name] * 2)  # Double entry for subscribers
                            response = f'{user_name} ได้ซัพทำให้ได้โชคคูณสอง.'
                        else:
                            self.giveaway_entries.append(user_name)
                            response = f'{user_name} ได้เข้าร่วม.'
                        self.save_giveaway_entries()
                    else:
                        response = f'{user_name}, มีรายชื่อแล้ว.'
                    await message.channel.send(response)
                    logger.info(f'Bot: {response}')

                await self.handle_commands(message)
        except Exception as e:
            logger.error(f'Error handling message: {e}')

    @commands.command(name='enter')
    async def enter(self, ctx):
        user_name = ctx.author.name
        user_id = ctx.author.id
        if user_name not in self.giveaway_entries:
            is_sub = await is_subscriber(user_id)
            if is_sub:
                self.giveaway_entries.extend([user_name] * 2) # Double entry for subscribers
                response = f'{user_name} ได้ซัพทำให้ได้โชคคูณสอง.'
            else:
                self.giveaway_entries.append(user_name)
                response = f'{user_name} ได้เข้าร่วม.'
            self.save_giveaway_entries()

        else:
            response = f'{user_name}, มีรายชื่อแล้ว.'
        await ctx.send(response)
        logger.info(f'Bot: {response}')

    @commands.command(name='random')
    async def random(self, ctx):
        if ctx.author.is_mod:
            if self.giveaway_entries:
                winner = random.choice(self.giveaway_entries)
                print(winner)
                await update_winner_file(winner)

                scene_name = "Scene"
                source_name = "wheel"

                if ws.identified:
                    await toggleobs(scene_name,source_name)
                else:
                    print("OBS WebSocket not connected, skipping toggle.")

                response = f'ยินดีด้วยกับ {winner}! คุณคือผู้ถูกเลือก ?!?!!!'

            else:
                response = 'No entries in the giveaway yet.'
        else:
            response = 'Only moderators can random the giveaway.'
        await ctx.send(response)
        logger.info(f'Bot: {response}')

    @commands.command(name='reset')
    async def reset(self, ctx):
        if ctx.author.is_mod:
            self.giveaway_entries = []
            self.save_giveaway_entries()
            response = 'The giveaway has been reset.'
        else:
            response = 'Only moderators can reset the giveaway.'
        await ctx.send(response)
        logger.info(f'Bot: {response}')

    @commands.command(name='check')
    async def check(self, ctx):
        if ctx.author.is_mod:
            user_list = self.giveaway_entries
            response = "User in list : " + ", ".join(user_list)
        else:
            response = 'Only moderators can use.'
        await ctx.send(response)
        logger.info(f'Bot: {response}')

async def init_obs():
    try:
        await ws.connect()
        await ws.wait_until_identified()
        print("OBS WebSocket connected and identified.")
    except Exception as e:
        logger.error(f"Failed to connect and identify with OBS WebSocket: {e}")

async def close_obs():
    await ws.disconnect()

async def bot_main():
    bot = Bot()
    await bot.start()

async def main():
    logger.info(f'Starting bot in {CHANNEL_NAME} . . .')

    try:
        await init_obs()  # Initialize OBS WebSocket connection
        await bot_main()  # Start the bot and keep it running
    finally:
        await close_obs()  # Ensure WebSocket is closed properly
        logger.info('Done...')

if __name__ == "__main__":
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(f'Bot process started at {start_time}')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot process interrupted by user.')
    finally:
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info(f'Bot process stopped at {end_time}')
