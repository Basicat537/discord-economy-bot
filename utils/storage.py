import json
import os
from datetime import datetime

class JsonStorage:
    def __init__(self, filename):
        self.filename = filename
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Create storage file if it doesn't exist"""
        if not os.path.exists(self.filename):
            directory = os.path.dirname(self.filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(self.filename, 'w') as f:
                json.dump({
                    'balances': {},
                    'linked_accounts': {},
                    'last_link_attempt': {}
                }, f)

    def _load_data(self):
        """Load data from storage file"""
        with open(self.filename, 'r') as f:
            return json.load(f)

    def _save_data(self, data):
        """Save data to storage file"""
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_balance(self, user_id):
        """Get user's balance"""
        data = self._load_data()
        return data.get('balances', {}).get(str(user_id), 0)

    def add_coins(self, user_id, amount):
        """Add coins to user's balance"""
        data = self._load_data()
        if 'balances' not in data:
            data['balances'] = {}
        data['balances'][str(user_id)] = data['balances'].get(str(user_id), 0) + amount
        self._save_data(data)

    def remove_coins(self, user_id, amount):
        """Remove coins from user's balance"""
        data = self._load_data()
        current_balance = data.get('balances', {}).get(str(user_id), 0)
        if current_balance < amount:
            raise ValueError("Недостаточно средств")
        data['balances'][str(user_id)] = current_balance - amount
        self._save_data(data)

    def transfer_coins(self, sender_id, recipient_id, amount):
        """Transfer coins between users"""
        self.remove_coins(sender_id, amount)
        self.add_coins(recipient_id, amount)

    def link_minecraft_account(self, discord_id, minecraft_username):
        """Link Discord ID to Minecraft username"""
        data = self._load_data()
        if 'linked_accounts' not in data:
            data['linked_accounts'] = {}

        # Проверяем, не привязан ли уже этот Minecraft аккаунт
        for existing_id, existing_name in data['linked_accounts'].items():
            if existing_name == minecraft_username:
                raise ValueError("Этот Minecraft аккаунт уже привязан к другому Discord пользователю")

        data['linked_accounts'][str(discord_id)] = minecraft_username
        self._save_data(data)

    def unlink_minecraft_account(self, discord_id):
        """Unlink Minecraft account from Discord ID"""
        data = self._load_data()
        if 'linked_accounts' in data and str(discord_id) in data['linked_accounts']:
            del data['linked_accounts'][str(discord_id)]
            self._save_data(data)

    def get_minecraft_username(self, discord_id):
        """Get Minecraft username linked to Discord ID"""
        data = self._load_data()
        return data.get('linked_accounts', {}).get(str(discord_id))

    def get_discord_id_by_minecraft(self, minecraft_username):
        """Get Discord ID linked to Minecraft username"""
        data = self._load_data()
        for discord_id, name in data.get('linked_accounts', {}).items():
            if name == minecraft_username:
                return discord_id
        return None