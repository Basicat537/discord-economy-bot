from aiohttp import web
import json
from utils.storage import JsonStorage
import os
import hashlib
import hmac

class APIServer:
    def __init__(self, storage):
        self.app = web.Application()
        self.storage = storage
        self.api_key = os.getenv('API_KEY', 'default_key')  # Для безопасной коммуникации
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/balance/{user_id}', self.get_balance)
        self.app.router.add_post('/balance/modify', self.modify_balance)
        self.app.router.add_get('/balance/test', self.test_connection)  # Добавляем тестовый эндпоинт

    def verify_signature(self, data, signature):
        """Verify request signature for security"""
        expected = hmac.new(
            self.api_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def test_connection(self, request):
        """Test endpoint to verify API connectivity"""
        signature = request.headers.get('X-Signature')

        if not signature or not self.verify_signature('test', signature):
            return web.Response(status=403, text='Invalid signature')

        return web.Response(text='API is working!')

    async def get_balance(self, request):
        """Get user balance endpoint"""
        user_id = request.match_info['user_id']
        signature = request.headers.get('X-Signature')

        if not signature or not self.verify_signature(user_id, signature):
            return web.Response(status=403, text='Invalid signature')

        balance = self.storage.get_user_balance(user_id)
        return web.Response(text=str(balance))

    async def modify_balance(self, request):
        """Modify user balance endpoint"""
        try:
            data = await request.json()
            signature = request.headers.get('X-Signature')

            if not signature or not self.verify_signature(
                f"{data['user_id']}{data['amount']}{data['operation']}", 
                signature
            ):
                return web.Response(status=403, text='Invalid signature')

            user_id = data['user_id']
            amount = int(data['amount'])
            operation = data['operation']

            if operation == 'add':
                self.storage.add_coins(user_id, amount)
            elif operation == 'remove':
                self.storage.remove_coins(user_id, amount)
            else:
                return web.Response(status=400, text='Invalid operation')

            return web.Response(text='Success')
        except Exception as e:
            return web.Response(status=400, text=str(e))

    async def start(self):
        """Start API server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        print("Starting API server on http://0.0.0.0:5000")  # Добавляем лог
        await site.start()
        print("API server started successfully")  # Добавляем лог