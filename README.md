# Discord Economy Bot

Бот для Discord с системой экономики и интеграцией с Minecraft через API.

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` с переменными окружения:
```env
DISCORD_TOKEN=ваш_токен_бота
API_KEY=ваш_секретный_ключ  # Тот же ключ, что используется в плагине Minecraft
```

3. Настройте `config.yml` при необходимости:
- Измените префикс команд
- Настройте параметры экономики
- Укажите путь к файлам данных и логов

## Запуск

```bash
python bot.py
```

## API Endpoints

- GET `/test` - Проверка работы API
- GET `/balance/{user_id}` - Получить баланс пользователя
- POST `/transfer` - Выполнить перевод между пользователями

Все запросы должны содержать заголовок `X-Signature` с HMAC-SHA256 подписью данных.

## Команды бота

- `!balance [@пользователь]` - Показать баланс
- `!pay @пользователь сумма` - Перевести деньги

## Безопасность

- API ключ должен храниться в переменных окружения
- Все запросы к API должны быть подписаны
- Используйте HTTPS при размещении в интернете

## Интеграция с Minecraft

Плагин `EconomyBridge` использует этот API для:
1. Синхронизации балансов между игрой и Discord
2. Обработки транзакций
3. Проверки балансов

## Логи

Логи сохраняются в файл, указанный в конфигурации (по умолчанию `logs/bot.log`).
