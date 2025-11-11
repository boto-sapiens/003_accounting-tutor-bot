# Quick Start Guide

## Статус

✅ **Бот успешно запущен и работает!**

- **Имя бота**: @DEV_goryunova_live_bot
- **Статус**: 🟢 Онлайн
- **Контейнер**: goryunova-live-bot (запущен)
- **Версия**: 0.1

## Проверка работы

### 1. Откройте бота в Telegram
```
https://t.me/DEV_goryunova_live_bot
```

### 2. Отправьте команду /start

Бот должен ответить: **"Привет! Бот запущен."**

## Управление контейнером

### Просмотр логов
```bash
cd /home/tomcat/projects/goryunova-live-bot
docker compose logs -f
```

### Перезапуск
```bash
docker compose restart
```

### Остановка
```bash
docker compose down
```

### Повторный запуск
```bash
docker compose up -d
```

### Проверка статуса
```bash
docker compose ps
```

## Структура проекта

```
goryunova-live-bot/
├── bot/
│   ├── src/
│   │   ├── __init__.py
│   │   └── main.py          # Основной файл бота
│   └── __init__.py
├── logs/                     # Логи (создается автоматически)
├── config.py                 # Конфигурация
├── requirements.txt          # Зависимости Python
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Docker Compose конфигурация
├── .env                     # Переменные окружения (токен)
├── README.md                # Основная документация
├── QUICKSTART.md           # Это файл
└── send_report.sh          # Скрипт для отправки отчета

```

## Основные характеристики

- **Framework**: aiogram 3.3.0
- **Python**: 3.11
- **Deployment**: Docker + Docker Compose
- **Restart policy**: unless-stopped (автоматический перезапуск)

## Что дальше?

1. ✅ Бот запущен и работает
2. 📱 Откройте @DEV_goryunova_live_bot в Telegram
3. 💬 Отправьте /start
4. 🎉 Получите ответ от бота

## Добавление новых команд

Отредактируйте файл `bot/src/main.py`:

```python
@router.message(Command("your_command"))
async def cmd_your_command(message: Message):
    """Your command handler"""
    await message.answer("Your response")
```

После изменений:
```bash
docker compose restart
```

## Troubleshooting

### Бот не отвечает
```bash
# Проверьте логи
docker compose logs -f

# Перезапустите контейнер
docker compose restart
```

### Проверка, что бот онлайн
```bash
curl -s 'https://api.telegram.org/bot8291776459:AAEFzDtWSyulItH4YlAzcAPB0YclUdT-a78/getMe' | python3 -m json.tool
```

Должен вернуть:
```json
{
    "ok": true,
    "result": {
        "username": "DEV_goryunova_live_bot",
        "first_name": "DEV_goryunova_live_bot"
    }
}
```

