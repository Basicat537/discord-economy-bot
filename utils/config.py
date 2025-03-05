import os

# Bot configuration
PREFIX = '/'
DEFAULT_BALANCE = 1000  # Starting balance

# Currency settings
CURRENCY = {
    'NAME': 'монет',
    'SYMBOL': '💰',
    'FORMAT': '{amount:,} {currency}'  # Example: "1,000 монет"
}

# Service levels configuration
SERVICE_LEVELS = {
    'levels': [
        {
            'id': 1,
            'name': 'Бронзовый',
            'emoji': '🥉',
            'required_balance': 10000,
            'color': 0xCD7F32,
            'benefits': [
                'Ежедневный бонус: 100 монет',
                'Множитель наград: 1.1x'
            ]
        },
        {
            'id': 2,
            'name': 'Серебряный',
            'emoji': '🥈',
            'required_balance': 50000,
            'color': 0xC0C0C0,
            'benefits': [
                'Ежедневный бонус: 300 монет',
                'Множитель наград: 1.25x'
            ]
        },
        {
            'id': 3,
            'name': 'Золотой',
            'emoji': '🥇',
            'required_balance': 100000,
            'color': 0xFFD700,
            'benefits': [
                'Ежедневный бонус: 500 монет',
                'Множитель наград: 1.5x'
            ]
        }
    ],
    'default_color': 0x7289DA
}

# Role settings
REQUIRED_ROLES = {
    'ADMIN': 'Admin',
    'MODERATOR': 'Moderator',
    'VIP': 'VIP'
}

# Permission levels (higher number = more permissions)
PERMISSION_LEVELS = {
    'DEFAULT': 0,
    'VIP': 1,
    'MODERATOR': 2,
    'ADMIN': 3
}

# Command permissions configuration
COMMAND_PERMISSIONS = {
    # Basic commands
    'help': {'level': 0, 'roles': []},
    'balance': {'level': 0, 'roles': []},
    'send': {'level': 0, 'roles': []},
    'top': {'level': 0, 'roles': []},
    'level': {'level': 0, 'roles': []},

    # Admin commands
    'admin_set': {'level': 3, 'roles': ['ADMIN']},
    'admin_reset': {'level': 3, 'roles': ['ADMIN']},
    'set_currency': {'level': 3, 'roles': ['ADMIN']},
    'set_permission': {'level': 3, 'roles': ['ADMIN']},
    'get_command_permissions': {'level': 3, 'roles': ['ADMIN']},
    'add_level': {'level': 3, 'roles': ['ADMIN']},
    'edit_level': {'level': 3, 'roles': ['ADMIN']},
    'remove_level': {'level': 3, 'roles': ['ADMIN']}
}

# Error messages
ERRORS = {
    'INSUFFICIENT_FUNDS': '❌ Недостаточно средств на счете!',
    'INVALID_AMOUNT': '❌ Сумма должна быть положительной!',
    'ECONOMY_MODULE_ERROR': '❌ Ошибка: модуль экономики не доступен',
    'NO_PERMISSION': '❌ У вас нет прав для выполнения этой команды!',
    'ROLE_NOT_FOUND': '❌ Требуемая роль не найдена на сервере!',
    'INVALID_PERMISSION_LEVEL': '❌ Неверный уровень прав доступа!',
    'COMMAND_NOT_FOUND': '❌ Команда не найдена!',
    'LEVEL_NOT_FOUND': '❌ Указанный уровень не найден!',
    'INVALID_LEVEL_ID': '❌ Неверный ID уровня!'
}