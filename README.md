# Telegram PDF Bot

Бот для конвертации PDF файлов в текст.  
- Приветствие при старте.
- Кнопки для удобного управления.
- Обработка больших PDF через FastAPI.
- OCR через Tesseract.

## Переменные окружения

- `TELEGRAM_TOKEN` - токен бота от BotFather
- `DOMAIN` - публичный URL проекта на Railway
- `TESSETACT_CMD` - путь к Tesseract для OCR

## Деплой на Railway

1. Создать проект на Railway.
2. Добавить переменные окружения.
3. Положить `railway.json` в корень проекта.
4. Залить проект в GitHub и подключить к Railway.
