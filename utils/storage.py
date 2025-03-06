import json
import os
from datetime import datetime, timedelta

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
                    'daily_claims': {},
                    'linked_accounts': {}
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
        return data.get('balances', {}).get(user_id, 0)

    def add_coins(self, user_id, amount):
        """Add coins to user's balance"""
        data = self._load_data()
        if 'balances' not in data:
            data['balances'] = {}
        data['balances'][user_id] = data['balances'].get(user_id, 0) + amount
        self._save_data(data)

    def remove_coins(self, user_id, amount):
        """Remove coins from user's balance"""
        data = self._load_data()
        current_balance = data.get('balances', {}).get(user_id, 0)
        if current_balance < amount:
            raise ValueError("Insufficient funds")
        data['balances'][user_id] = current_balance - amount
        self._save_data(data)

    def transfer_coins(self, sender_id, recipient_id, amount):
        """Transfer coins between users"""
        self.remove_coins(sender_id, amount)
        self.add_coins(recipient_id, amount)

    def add_daily_reward(self, user_id):
        """Add daily reward to user"""
        data = self._load_data()
        now = datetime.now().isoformat()
        last_claim = data.get('daily_claims', {}).get(user_id)
        
        if last_claim and datetime.fromisoformat(last_claim) + timedelta(days=1) > datetime.now():
            raise ValueError("You already claimed your daily reward today!")

        reward_amount = 100
        self.add_coins(user_id, reward_amount)
        
        if 'daily_claims' not in data:
            data['daily_claims'] = {}
        data['daily_claims'][user_id] = now
        self._save_data(data)
        return reward_amount

    def set_minecraft_link(self, user_id, minecraft_username):
        """Link Discord user to Minecraft username"""
        data = self._load_data()
        if 'linked_accounts' not in data:
            data['linked_accounts'] = {}
        data['linked_accounts'][user_id] = minecraft_username
        self._save_data(data)

    def remove_minecraft_link(self, user_id):
        """Remove Minecraft link for user"""
        data = self._load_data()
        if 'linked_accounts' in data and user_id in data['linked_accounts']:
            del data['linked_accounts'][user_id]
            self._save_data(data)

    def get_minecraft_username(self, user_id):
        """Get linked Minecraft username for user"""
        data = self._load_data()
        return data.get('linked_accounts', {}).get(user_id)

    def give_minecraft_reward(self, user_id):
        """Give reward for linked Minecraft account"""
        if not self.get_minecraft_username(user_id):
            raise ValueError("You need to link your Minecraft account first!")
        
        reward_amount = 50
        self.add_coins(user_id, reward_amount)
        return reward_amount
