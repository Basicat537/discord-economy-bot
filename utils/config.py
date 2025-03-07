import os

# Bot configuration
PREFIX = '/'
DEFAULT_BALANCE = 1000  # Starting balance

# Currency settings
CURRENCY = {
    'NAME': 'монет',
    'SYMBOL': '💰'
}

# Default color for embeds when no service level color is available
DEFAULT_COLOR = 0x7289DA

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

# Service levels configuration
SERVICE_LEVELS = {
    'default_color': DEFAULT_COLOR
}