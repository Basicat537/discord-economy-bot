import os

# Bot configuration
PREFIX = '/'
DEFAULT_BALANCE = 1000  # Changed to give users starting money

# Currency settings
CURRENCY = {
    'NAME': 'монет',
    'SYMBOL': '💰',
    'FORMAT': '{amount:,} {currency}'  # Example: "1,000 монет"
}

# Role settings
REQUIRED_ROLES = {
    'ADMIN': 'Admin',       # Role name for admin commands
    'MODERATOR': 'Moderator', # Role name for moderation commands
    'VIP': 'VIP'           # Role name for VIP features
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
    # Economy commands
    'balance': {'level': 0, 'roles': []},
    'send': {'level': 0, 'roles': []},
    'top': {'level': 0, 'roles': []},

    # Admin commands
    'admin_set': {'level': 3, 'roles': ['ADMIN']},
    'admin_reset': {'level': 3, 'roles': ['ADMIN']},
    'set_currency': {'level': 3, 'roles': ['ADMIN']},

    # Permission management
    'set_command_permission': {'level': 3, 'roles': ['ADMIN']},
    'get_command_permissions': {'level': 3, 'roles': ['ADMIN']}
}

# Error messages
ERRORS = {
    'INSUFFICIENT_FUNDS': '❌ Недостаточно средств на счете!',
    'INVALID_AMOUNT': '❌ Сумма должна быть положительной!',
    'ECONOMY_MODULE_ERROR': '❌ Ошибка: модуль экономики не доступен',
    'NO_PERMISSION': '❌ У вас нет прав для выполнения этой команды!',
    'ROLE_NOT_FOUND': '❌ Требуемая роль не найдена на сервере!',
    'INVALID_PERMISSION_LEVEL': '❌ Неверный уровень прав доступа!',
    'COMMAND_NOT_FOUND': '❌ Команда не найдена!'
}