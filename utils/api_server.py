from aiohttp import web
import json
from utils.storage import JsonStorage
import os
import hashlib
import hmac
import asyncio

class APIServer:
    def __init__(self, storage):
        self.app = web.Application()
        self.storage = storage
        self.api_key = os.getenv('API_KEY')  # Получаем ключ из переменной окружения
        if not self.api_key:
            raise ValueError("API_KEY environment variable is not set!")
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/balance/{user_id}', self.get_balance)
        self.app.router.add_post('/transfer', self.transfer_money)
        self.app.router.add_get('/test', self.test_connection)

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
        return web.json_response({'status': 'ok', 'message': 'API is working!'})

    async def get_balance(self, request):
        """Get user balance endpoint"""
        user_id = request.match_info['user_id']
        signature = request.headers.get('X-Signature')

        if not signature or not self.verify_signature(user_id, signature):
            return web.Response(status=403, text='Invalid signature')

        balance = self.storage.get_user_balance(user_id)
        return web.json_response({'balance': balance})

    async def transfer_money(self, request):
        """Transfer money between users"""
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
                self.storage.transfer_coins(from_id, to_id, amount)
                return web.json_response({
                    'status': 'success',
                    'message': 'Transfer completed',
                    'from_balance': self.storage.get_user_balance(from_id),
                    'to_balance': self.storage.get_user_balance(to_id)
                })
            except ValueError as e:
                return web.Response(status=400, text=str(e))

        except Exception as e:
            return web.Response(status=400, text=str(e))

    async def start(self):
        """Start API server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
        print("API server started on http://0.0.0.0:5000")

        # Добавляем блокировку, чтобы сервер не завершался
        await asyncio.Event().wait()