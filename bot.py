import asyncio
import logging
import os
import random
import json
import time
import pytz
import aiohttp
from datetime import datetime
from collections import defaultdict
from twitchio.ext import commands
import simpleobsws

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(BASE_DIR, 'bot.log')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

parameters = simpleobsws.IdentificationParameters()
parameters.eventSubscriptions = (1 << 0) | (1 << 2)
ws = simpleobsws.WebSocketClient(url='ws://localhost:4444', password='risBs8nGQX38EpEh', identification_parameters=parameters)

TOKENS_FILE = os.path.join(BASE_DIR, 'data/tokens.json')
def load_tokens():
    with open(TOKENS_FILE, 'r') as f:
        return json.load(f)

TOKENS = load_tokens()
CHANNEL_NAME = 'urxi_'
BROADCASTER_ID = TOKENS['BROADCASTER_ID'] 
MODERATOR_ID = TOKENS['MODERATOR_ID']
TWITCH_CLIENT_ID = TOKENS['TWITCH_CLIENT_ID']
TWITCH_OAUTH_TOKEN = TOKENS['TWITCH_OAUTH_TOKEN']
COUNTER_FILE = os.path.join(BASE_DIR, 'data/counters.json')
COMMANDS_FILE = os.path.join(BASE_DIR, 'data/commands.json')
MONEY_FILE = os.path.join(BASE_DIR, 'data/money.json')
FOOD_FILE = os.path.join(BASE_DIR, 'data/food.json')
BULLET_FILE = os.path.join(BASE_DIR, 'gunhtml/bullet.json')
class Cooldown:
    def __init__(self, rate, per):
        self.rate = rate
        self.per = per
        self.cooldowns = defaultdict(lambda: 0)

    def check(self, user_id):
        now = time.time()
        if now - self.cooldowns[user_id] < self.per:
            return False
        self.cooldowns[user_id] = now
        return True


def load_counters():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            try:
                return json.load(f)
            except (ValueError, json.JSONDecodeError):
                return {"sharp": 0, "cute": 0}
    return {"sharp": 0, "cute": 0}


def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, 'r') as f:
            try:
                return json.load(f)
            except (ValueError, json.JSONDecodeError):
                return {}
    return


def load_money():
    if os.path.exists(MONEY_FILE):
        with open(MONEY_FILE, 'r') as f:
            try:
                return json.load(f)
            except (ValueError, json.JSONDecodeError):
                return {}
    return {}

def load_foods():
    if os.path.exists(FOOD_FILE):
        try:
            with open(FOOD_FILE, 'r', encoding='utf-8') as f:
                foods = json.load(f)
                return foods
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")  # Debugging line
            return []
    print("File not found!")  # Debugging line
    return []

def save_bullet(bullet_position):
    with open(BULLET_FILE, 'w') as f:
        json.dump(bullet_position, f, indent=4)

async def get_user_id(username):
    url = 'https://api.twitch.tv/helix/users'
    headers = {
        'Authorization': f'Bearer {TWITCH_OAUTH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
    }
    params = {
        'login': username
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                logger.info(f"API Response:{data}")
                if data['data']:
                    return data['data'][0]['id']
                else:
                    logger.error(f'User {username} not found.')
                    return None
            else:
                logger.error(f'Failed to get user ID for {username}. Response: {resp.status} - {await resp.text()}')
                return None


async def get_category_id(game_name):
    url = "https://api.twitch.tv/helix/games"
    headers = {
        "Authorization": f"Bearer {TWITCH_OAUTH_TOKEN}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    params = {"name": game_name}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"API Response:{data}")
                if data.get('data'):
                    return data['data'][0]['id']
            return None


async def update_channel_category(category_id):
    url = f"https://api.twitch.tv/helix/channels?broadcaster_id={BROADCASTER_ID}"
    headers = {
        "Authorization": f"Bearer {TWITCH_OAUTH_TOKEN}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    params = {"broadcaster_id": BROADCASTER_ID}
    json_data = {"game_id": category_id}

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, params=params, json=json_data) as response:
            if response.status != 204:
                raise Exception(f"Failed to update category. Status code: {response.status}, Response: {await response.text()}")


async def timeout_user(user_id, duration, reason):
    url = f'https://api.twitch.tv/helix/moderation/bans?broadcaster_id={BROADCASTER_ID}&moderator_id={MODERATOR_ID}'
    headers = {
        'Authorization': f'Bearer {TWITCH_OAUTH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json',
    }
    json_data = {
        "data": {
            "user_id": user_id,
            "duration": duration,
            "reason": reason
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_data) as resp:
            if resp.status == 200:
                logger.info(f'Successfully timed out user {user_id} for {duration} seconds.')
            else:
                logger.error(f'Failed to timeout user {user_id}. Response: {resp.status} - {await resp.text()}')


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TWITCH_OAUTH_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick='Urxi_',
            prefix='!',
            initial_channels=[CHANNEL_NAME]
        )
        self.cooldowns = {
            "sharp": Cooldown(rate=1, per=10),  # 1 use per 10 seconds
            "cute": Cooldown(rate=1, per=10),
            "noob": Cooldown(rate=1, per=10)
        }
        self.counters = load_counters()
        self.commands_responses = load_commands()
        self.moneys = load_money()
        self.viewers = set()
        self.active_bets = {}

    def save_counters(self):
        with open(COUNTER_FILE, 'w') as f:
            json.dump(self.counters, f, indent = 4)

    def save_commands(self):
        with open(COMMANDS_FILE, 'w') as f:
            json.dump(self.commands_responses, f, indent = 4)

    def save_moneys(self):
        with open(MONEY_FILE, 'w') as f:
            json.dump(self.moneys, f, indent=4)

    async def event_join(self, channel, user):
        if user.name != self.nick:
            self.viewers.add(user.name)
            logger.info(f'Bot : {user.name} has joined the chat.')

    async def event_part(self, user):
        if user.name in self.viewers:
            self.viewers.remove(user.name)
            logger.info(f'Bot : {user.name} has left the chat.')
            
    async def event_ready(self):
        logger.info(f'Logged in as {self.nick}')
        logger.info(f'Connected to {CHANNEL_NAME}')
        #await self.loop.create_task(self.auto_message_task())

    ####################################################################
    async def auto_message_task(self):
        while True:
              # Wait for 30 minutes
            channel = self.get_channel(CHANNEL_NAME)
            if channel:
                message = "❤"
                await channel.send(message)
                logger.info(f'Bot : {message}')
                await asyncio.sleep(1800)
                message = "!!!"
                await channel.send(message)
                logger.info(f'Bot : {message}')
                await asyncio.sleep(1800)
    ####################################################################

    async def event_message(self, message):
        try:
            if message.author:
                logger.info(f'{message.author.name}: {message.content}')

                command = message.content.lower()

                if command in self.commands_responses:
                    response = self.commands_responses[command]
                    await message.channel.send(response)
                    logger.info(f'Bot: {response}')

                if command.startswith('คม') or 'ns' == command:
                    if not self.cooldowns["sharp"].check(message.author.id):
                        return
                    self.counters["sharp"] += 1
                    self.save_counters()
                    response = f'ยิงคมไปแล้วทั้งหมด {self.counters["sharp"]} ครั้ง'
                    await message.channel.send(response)
                    logger.info(f'Bot: {response}')

                elif command.startswith('159743568'):
                    if not self.cooldowns["cute"].check(message.author.id):
                        return
                    self.counters["cute"] += 1
                    self.save_counters()
                    response = f'น่ารักไปแล้วทั้งหมด {self.counters["cute"]} ครั้ง'
                    await message.channel.send(response)
                    logger.info(f'Bot: {response}')

                elif command == 'noob':
                    if not self.cooldowns["noob"].check(message.author.id):
                        return
                    response = f'นูปพ่องมึงอะไอsuss'
                    await message.channel.send(response)
                    logger.info(f'Bot: {response}')
                ####################################################################
                await self.handle_commands(message)
        except Exception as e:
            logger.error(f'Error handling message: {e}')


    @commands.command(name='addcom')
    async def addcom(self, ctx):
        if ctx.author.is_mod:
            parts = ctx.message.content.split(maxsplit=2)
            if len(parts) < 3:
                await ctx.send('ลอง : !addcom <command> <response>.')
                return

            command = parts[1]
            response = parts[2]
            if command in self.commands_responses:
                await ctx.send(f'command {command} นี้มีอยู่แล้ว. ลอง !editcom แก้ไขแทน.')
                return

            self.commands_responses[command] = response
            self.save_commands()
            await ctx.send(f'Command {command} นี้ถูกเพิ่มเสร็จสิ้นเรียบร้อย.')
            logger.info(f'Bot: Command {command} has been added with response: {response}')

    @commands.command(name='editcom')
    async def editcom(self, ctx):
        if ctx.author.is_mod:
            parts = ctx.message.content.split(maxsplit=2)
            if len(parts) < 3:
                await ctx.send('ลอง : !editcom <command> <response>')
                return

            command = parts[1]
            response = parts[2]
            self.commands_responses[command] = response
            self.save_commands()
            await ctx.send(f'Command {command} นี้ถูกแก้ไขเรียบร้อย.')
            logger.info(f'Bot: Command {command} has been updated to: {response}')

    @commands.command(name='listcom')
    async def listcom(self, ctx):
        commands_list = list(self.commands_responses.keys())
        response = "commands ที่ใช้ได้ : " + ", ".join(commands_list)
        await ctx.send(response)
        logger.info(f'Bot: {response}')

    @commands.command(name='time')
    async def time(self, ctx):
        tz = pytz.timezone('Asia/Bangkok')  # GMT+7 timezone
        now = datetime.now(tz)
        day = now.day
        suffix = 'th' if 11 <= day % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        formatted_time = now.strftime(f"%B {day}{suffix} %Y, %I:%M:%S %p GMT%z")
        await ctx.send(f'เวลาตอนนี้คือ {formatted_time}.')
        logger.info(f'Bot: {formatted_time}')

    ####################################################################

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='ต่อย')
    async def hit(self, ctx):
        # Split the message content to find the username
        parts = ctx.message.content.split()
        if len(parts) == 2:
            target = parts[1]  # Get the username directly
            hits = random.randint(1, 100)
            response = f'@{ctx.author.name} ต่อย {target} ไป {hits} ครั้ง!'
        else:
            response = 'ลอง : !ต่อย @username'
        await ctx.send(response)
        logger.info(f'Bot : {response}')

    @commands.command(name='so')
    async def so(self, ctx):
        parts = ctx.message.content.split()
        try:
            if ctx.author.is_mod:
                target = parts[1]
                response = f"ฝากกดติดตามคนน่ารักได้ที่ twitch.tv/{target[1:]}"
                await ctx.send(response)
                logger.info(f'Bot: {response}')        
            else:
                response = f"{ctx.author.name} ใช้ได้เฉพาะดาบนะค้าบ 😓."
                await ctx.send(response)
                logger.info(f'Bot: {response}')
        except Exception:
                response = f"{ctx.author.name} เป็นดาบได้ไงเนี่ย ลืมแท็คช่อง"
                await ctx.send(response)
                logger.info(f'Bot: {response}')
    ####################################################################

    #@commands.cooldown(rate=1, per=120, bucket=commands.Bucket.channel)
    @commands.command(name='russianroulette')
    async def russianroulette(self, ctx ):
        parts = ctx.message.content.split()
        if len(parts) == 2:
            user = ctx.author.name
            target = parts[1]
            user_id = ctx.author.id
            target_user_id = await get_user_id(target[1:])
            players = [(target[1:], target_user_id),(user, user_id)]
            bullet_position = random.randint(1, 6)
            save_bullet(bullet_position)
            scene_name = "Scene"
            source_name = "gun"
            duration = 10

            if ws.identified:
                await toggleobs(scene_name, source_name, duration)
            else:
                print("OBS WebSocket not connected, skipping toggle.")

            for shot in range(1, 7):
                await asyncio.sleep(4)
                current_player, current_player_id = players[shot % 2]
                other_player, other_player_id = players[(shot + 1) % 2]

                if bullet_position == shot:
                    response = f"💥 กระสุนที่ {shot}: {current_player} ถูกฟลิ้คเข้าหัวไปแบบคม ๆ ทำให้แพ้เกมนี้และจะถูก timeout 2 นาที 🔥💀💀💀💥."
                    await ctx.send(response)
                    logger.info(f'Bot: {response}')
                    await asyncio.sleep(10)
                    if current_player_id == BROADCASTER_ID:
                        response = f"แต่พอดีว่า {current_player} เป็นคนมีอิทธิพลเปิดการ์ดชุบชีวิตและทำการยิงสวนไปอีกคนแทน อิอิ."
                        await ctx.send(response)
                        logger.info(f'Bot: {response}')
                        await timeout_user(other_player_id, 120, "Lost in Russian Roulette game impossible to win 😈")
                    else:
                        response = f"{current_player} ถูก timeout 2 นาที."
                        await ctx.send(response)
                        logger.info(f'Bot: {response}')
                        await timeout_user(current_player_id, 120, "Lost in Russian Roulette game")
                    break
                else:
                    response = f"🔫 กระสุนที่ {shot}: ไม่มีกระสุน! {current_player} รอดตัวไปนะเรา."
                    await ctx.send(response)
                    logger.info(f'Bot: {response}')
            else:
                response = "รอดคู่ มันเป็นไปได้ไงว้ะ โค้ดกาก! 😅"
                await ctx.send(f"{response}")
                logger.info(f'Bot: {response}')
        else:
            response = "ลอง : !russianroulette <target>"
            await ctx.send(f"{response}")
            logger.info(f'Bot: {response}')

    @commands.command(name='game')
    async def change_game(self, ctx, *, game_name: str):
        if ctx.author.is_mod:
            try:
                category_id = await get_category_id(game_name)
                if category_id:
                    await update_channel_category(category_id)
                    response = f"เปลี่ยนหมวดหมู่เป็น : {game_name}."
                    await ctx.send(f"{response}")
                    logger.info(f'Bot: {response}')
                else:
                    response = f"หาหมวดหมู่นี้ไม่เจอ : {game_name}."
                    await ctx.send(f"{response}")
                    logger.info(f'Bot: {response}')
            except Exception as e:
                response = f"An error occurred: {str(e)}"
                await ctx.send(response)
                logger.info(f'Bot: {response}')
        else:
            response = f"ใช้ได้เฉพาะดาบนะค้าบ 😓."
            await ctx.send(f"{response}")
            logger.info(f'Bot: {response}')

    #@commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='coin')
    async def coin(self, ctx):
        parts = ctx.message.content.split()
        if len(parts) == 1:
            user_id = str(ctx.author.id)
            user_balance = self.moneys.get(user_id, 0)
            response = f"{ctx.author.mention}, คุณมีอยู่ {user_balance} เหรียญ."
            await ctx.send(response)
            logger.info(f'Bot: {response}')
        elif len(parts) == 2:
            target = parts[1]
            target_user_id = await get_user_id(target.lstrip("@"))
            user_balance = self.moneys.get(target_user_id, 0)
            response = f"{target.lstrip("@")}, มีอยู่ {user_balance} เหรียญ."
            await ctx.send(response)
            logger.info(f'Bot: {response}')
        elif len(parts) == 3 and ctx.author.is_mod:
            target = parts[1]
            amount = parts[2]
            amount = int(amount)
            target_user_id = await get_user_id(target.lstrip("@"))
            self.moneys[target_user_id] += amount
            response = f"ทำการเพิ่ม {amount} เหรียญ ให้แก่ {target.lstrip("@")} เป็นที่เรียบร้อย."
            self.save_moneys()
            await ctx.send(response)
            logger.info(f'Bot: {response}')
        else:
            response = "ลอง : !coin , optional : <target> , <amount>"
            await ctx.send(f"{response}")
            logger.info(f'Bot: {response}')
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='bet')
    async def bet(self, ctx, opponent: str = None, amount: int = None):
        try:
            self.moneys = load_money()
            if opponent is None or amount is None:
                response = "กรุณาระบุผู้ท้าชิงและจำนวนเหรียญที่ต้องการเดิมพัน : !bet <opponent> <amount>"
                await ctx.send(response)
                logger.info(f'Bot: {response}')
                return

            if amount <= 0:
                response = "ไม่สามารถใช้จำนวนเหรียญติดลบได้"
                await ctx.send(response)
                logger.info(f'Bot: {response}')
                return

            challenger = ctx.author.name
            opponent = opponent.lstrip('@')

            challenger_id = str(ctx.author.id)
            opponent_id = str(await get_user_id(opponent))

            if challenger_id not in self.moneys:
                self.moneys[challenger_id] = 1000
            if opponent_id not in self.moneys:
                self.moneys[opponent_id] = 1000
            self.save_moneys()

            if amount > self.moneys[challenger_id]:
                response = f"{challenger}, คุณมีเหรียญไม่พอที่จะวางเบท! ตอนนี้คุณมีเงินอยู่ {self.moneys[challenger_id]} เหรียญ."
                await ctx.send(response)
                logger.info(f'Bot: {response}')
                return
            if amount > self.moneys[opponent_id]:
                response = f"{opponent} มีเหรียญไม่พอที่จะตอบรับคำท้าเบทนี้!"
                await ctx.send(response)
                logger.info(f'Bot: {response}')
                return

            self.active_bets[opponent_id] = {'challenger': challenger, 'amount': amount}

            response = f"{challenger} ได้ส่งหมายศาลคำท้า {opponent} โดยที่จะเบท {amount} เหรียญ! พิมพ์ !accept ใน 30 วินาทีเพื่อยอมรับคำท้า."
            await ctx.send(response)
            logger.info(f'Bot: {response}')

            await asyncio.sleep(30)

            if opponent_id in self.active_bets:
                self.active_bets.pop(opponent_id)
                response = f"{opponent} ไม่ได้ยอมรับคำท้าในเวลาที่กำหนด คำท้าถูกยกเลิก."
                await ctx.send(response)
                logger.info(f'Bot: {response}')

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            response = "เกิดข้อผิดพลาด: กรุณาลองใหม่อีกครั้ง!"
            await ctx.send(response)
            logger.info(f'Bot: {response}')

    @commands.command(name='accept')
    async def accept(self, ctx):
        opponent = ctx.author.name
        opponent_id = str(ctx.author.id)

        if opponent_id not in self.active_bets:
            response = f"{opponent}, คุณไม่ได้อยู่รายชื่อที่ถูกคำท้า."
            await ctx.send(response)
            logger.info(f'Bot: {response}')
            return

        challenger = self.active_bets[opponent_id]['challenger']
        challenger_id = await get_user_id(challenger)

        bet = self.active_bets.pop(opponent_id)
        challenger = bet['challenger']
        amount = bet['amount']

        outcome = random.choice(["challenger", "opponent"])
        if outcome == "challenger":
            self.moneys[str(challenger_id)] += amount
            self.moneys[opponent_id] -= amount
            response = f"{challenger} ชนะไปในการเบทครั้งนี้ ! ได้รับ {amount} เหรียญไป !!!"
            await ctx.send(response)
            logger.info(f'Bot: {response}')
        else:
            self.moneys[str(challenger_id)] -= amount
            self.moneys[opponent_id] += amount
            response = f"{opponent} ชนะไปในการเบทครั้งนี้ ! ได้รับ {amount} เหรียญไป !!!"
            await ctx.send(response)
            logger.info(f'Bot: {response}')

        # Save updated money data
        self.save_moneys()

    @commands.command(name='กินไรดี')
    async def eatinthai(self, ctx):
        foods = load_foods()
        user_name = ctx.author.name

        if foods:
            food = random.choice(foods)
            food_name = food.get('name', 'อาหารไม่ทราบชื่อ')
            response = f"คุณ {user_name} วันนี้กิน {food_name} ดีมั้ย?"
            await ctx.send(response)
            logger.info(f'Bot: {response}')
        else:
            response = "ไม่มีอาหารในรายการ ลองเพิ่มอาหารก่อนนะ!"
            await ctx.send(response)
            logger.info(f'Bot: {response}')

async def toggleobs(scene_name,source_name, duration):
    if not ws or not ws.identified:
        print("OBS WebSocket is not connected or identified. Skipping OBS toggle.")
        return

    await toggle_source_visibility(scene_name, source_name, duration)
    print(f"Toggled visibility of {source_name} in OBS.")

async def get_scene_item_id(scene_name, source_name):
    response = await ws.call(simpleobsws.Request('GetSceneItemList', {'sceneName': scene_name}))
    if response.ok():
        for item in response.responseData['sceneItems']:
            if item['sourceName'] == source_name:
                return item['sceneItemId']
    print(f"Source '{source_name}' not found in scene '{scene_name}'.")
    return None

async def toggle_source_visibility(scene_name, source_name, duration):
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

async def init_obs():
    try:
        await ws.connect()
        await ws.wait_until_identified()
        print("OBS WebSocket connected and identified.")
    except Exception as e:
        logger.error(f"Failed to connect and identify with OBS WebSocket: {e}")

async def close_obs():
    await ws.disconnect()

async def main():
    logger.info(f'Starting bot in {CHANNEL_NAME} . . .')
    try:
        await init_obs()
        bot = Bot()
        await bot.start()
    finally:
        await close_obs()
        logger.info('Done ...')

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