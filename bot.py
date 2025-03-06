import os
import yaml
import logging
import discord
from discord.ext import commands
from aiohttp import web
import json
import hmac
import hashlib
from datetime import datetime

# Создаем директории, если они не существуют
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Загрузка конфигурации
with open('config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format=config['logging']['format'],
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()  # Добавляем вывод в консоль
    ]
)
logger = logging.getLogger('EconomyBot')

# Инициализация бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Для работы с участниками
bot = commands.Bot(command_prefix=config['bot']['prefix'], intents=intents)

# Класс для работы с экономикой
class EconomyManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.ensure_db_exists()

    def ensure_db_exists(self):
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({'balances': {}, 'minecraft_accounts': {}}, f)

    def load_data(self):
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_balance(self, user_id):
        data = self.load_data()
        return data['balances'].get(str(user_id), config['economy']['starting_balance'])

    def set_balance(self, user_id, amount):
        data = self.load_data()
        data['balances'][str(user_id)] = amount
        self.save_data(data)

    def transfer(self, from_id, to_id, amount):
        from_balance = self.get_balance(from_id)
        if from_balance < amount:
            raise ValueError("Недостаточно средств")

        to_balance = self.get_balance(to_id)
        self.set_balance(from_id, from_balance - amount)
        self.set_balance(to_id, to_balance + amount)

    def link_minecraft_account(self, user_id, minecraft_username):
        data = self.load_data()
        if str(user_id) in data['minecraft_accounts']:
            raise ValueError("У вас уже привязан Minecraft аккаунт")
        data['minecraft_accounts'][str(user_id)] = minecraft_username
        self.save_data(data)

    def unlink_minecraft_account(self, user_id):
        data = self.load_data()
        if str(user_id) in data['minecraft_accounts']:
            del data['minecraft_accounts'][str(user_id)]
            self.save_data(data)
        else:
            raise ValueError("У вас нет привязанного Minecraft аккаунта")

    def get_minecraft_username(self, user_id):
        data = self.load_data()
        return data['minecraft_accounts'].get(str(user_id))


# Инициализация экономики
economy = EconomyManager(config['database']['path'])

# API сервер
class APIServer:
    def __init__(self, bot, economy):
        self.app = web.Application()
        self.bot = bot
        self.economy = economy
        self.api_key = os.getenv('API_KEY')
        if not self.api_key:
            raise ValueError("API_KEY не установлен")
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/balance/{user_id}', self.get_balance)
        self.app.router.add_post('/transfer', self.transfer_money)
        self.app.router.add_get('/test', self.test_connection)

    def verify_signature(self, data, signature):
        expected = hmac.new(
            self.api_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def test_connection(self, request):
        signature = request.headers.get('X-Signature')
        if not signature or not self.verify_signature('test', signature):
            return web.Response(status=403, text='Invalid signature')
        return web.json_response({'status': 'ok', 'message': 'API is working!'})

    async def get_balance(self, request):
        user_id = request.match_info['user_id']
        signature = request.headers.get('X-Signature')

        if not signature or not self.verify_signature(user_id, signature):
            return web.Response(status=403, text='Invalid signature')

        balance = self.economy.get_balance(user_id)
        return web.json_response({'balance': balance})

    async def transfer_money(self, request):
        try:
            data = await request.json()
            signature = request.headers.get('X-Signature')

            signature_data = f"{data['from_id']}{data['to_id']}{data['amount']}"
            if not signature or not self.verify_signature(signature_data, signature):
                return web.Response(status=403, text='Invalid signature')

            from_id = data['from_id']
            to_id = data['to_id']
            amount = int(data['amount'])

            if amount <= 0:
                return web.Response(status=400, text='Amount must be positive')

            try:
                self.economy.transfer(from_id, to_id, amount)
                return web.json_response({
                    'status': 'success',
                    'message': 'Transfer completed',
                    'from_balance': self.economy.get_balance(from_id),
                    'to_balance': self.economy.get_balance(to_id)
                })
            except ValueError as e:
                return web.Response(status=400, text=str(e))

        except Exception as e:
            return web.Response(status=400, text=str(e))

# Команды бота
@bot.command(name='balance')
async def balance(ctx, member: discord.Member = None):
    """Показать баланс пользователя"""
    target = member or ctx.author
    balance = economy.get_balance(target.id)

    embed = discord.Embed(
        title="Баланс",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Пользователь",
        value=target.display_name,
        inline=False
    )
    embed.add_field(
        name="Баланс",
        value=f"{config['economy']['currency_symbol']} {balance} {config['economy']['currency_name']}",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command(name='pay')
async def pay(ctx, member: discord.Member, amount: int):
    """Перевести деньги другому пользователю"""
    try:
        economy.transfer(ctx.author.id, member.id, amount)
        embed = discord.Embed(
            title="Перевод выполнен",
            color=discord.Color.green()
        )
        embed.add_field(name="От", value=ctx.author.display_name, inline=True)
        embed.add_field(name="Кому", value=member.display_name, inline=True)
        embed.add_field(
            name="Сумма",
            value=f"{config['economy']['currency_symbol']} {amount} {config['economy']['currency_name']}",
            inline=False
        )
        await ctx.send(embed=embed)
    except ValueError as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

@bot.command(name='linkmc')
async def link_minecraft(ctx, minecraft_username: str):
    """Привязать Minecraft аккаунт к Discord"""
    try:
        economy.link_minecraft_account(ctx.author.id, minecraft_username)
        embed = discord.Embed(
            title="✅ Аккаунт привязан",
            description=f"Ваш Discord аккаунт успешно привязан к Minecraft нику: {minecraft_username}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Что дальше?",
            value="Теперь войдите на сервер Minecraft и используйте команду `/verify` для подтверждения привязки",
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f"User {ctx.author.id} linked Minecraft account: {minecraft_username}")
    except ValueError as e:
        await ctx.send(f"❌ Ошибка: {str(e)}")

@bot.command(name='unlinkmc')
async def unlink_minecraft(ctx):
    """Отвязать Minecraft аккаунт"""
    minecraft_username = economy.get_minecraft_username(ctx.author.id)
    if not minecraft_username:
        await ctx.send("❌ У вас нет привязанного Minecraft аккаунта")
        return

    economy.unlink_minecraft_account(ctx.author.id)
    embed = discord.Embed(
        title="✅ Аккаунт отвязан",
        description=f"Ваш Minecraft аккаунт ({minecraft_username}) успешно отвязан",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)
    logger.info(f"User {ctx.author.id} unlinked Minecraft account")

@bot.command(name='mcstatus')
async def minecraft_status(ctx):
    """Показать информацию о привязанном аккаунте"""
    minecraft_username = economy.get_minecraft_username(ctx.author.id)
    if not minecraft_username:
        await ctx.send("❌ У вас нет привязанного Minecraft аккаунта")
        return

    embed = discord.Embed(
        title="Статус Minecraft аккаунта",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Minecraft ник",
        value=minecraft_username,
        inline=False
    )
    embed.add_field(
        name="Discord",
        value=ctx.author.mention,
        inline=False
    )
    await ctx.send(embed=embed)

# Запуск бота и API сервера
async def start_api():
    api_server = APIServer(bot, economy)
    runner = web.AppRunner(api_server.app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        config['api']['host'],
        config['api']['port']
    )
    await site.start()
    logger.info(f"API server started on {config['api']['host']}:{config['api']['port']}")

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    await start_api()
    await bot.change_presence(activity=discord.Game(config['bot']['status']))

# Запуск бота
if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run(os.getenv('DISCORD_TOKEN'))