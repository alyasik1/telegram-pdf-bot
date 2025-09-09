# Telegram PDF Bot

Асинхронный Telegram-бот для конвертации PDF в текст. Поддерживает большие файлы (>50 МБ) через ссылки для скачивания, красивое приветствие с кнопками и быстрый отклик.

## Особенности

* Конвертация PDF в `.txt` с помощью PyPDF2.
* Асинхронная обработка файлов, чтобы бот не «замораживался».
* Для файлов >50 МБ — ссылка для скачивания через FastAPI.
* Красивое приветствие с интерактивными кнопками (`Конвертировать PDF`, `Помощь`).
* Быстрое реагирование на команды и сообщения.

## Требования

* Python 3.9+
* Telegram Bot API токен
* Библиотеки из `requirements.txt`

## Установка и запуск локально

1. Клонируйте репозиторий:

```bash
git clone https://github.com/ВАШ_USERNAME/telegram-pdf-bot.git
cd telegram-pdf-bot
```

2. Создайте и активируйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Установите переменные окружения:

```bash
export TELEGRAM_TOKEN="ваш_токен_бота"
export DOMAIN="http://localhost:8000"
```

> Windows PowerShell:

```powershell
setx TELEGRAM_TOKEN "ваш_токен_бота"
setx DOMAIN "http://localhost:8000"
```

5. Запустите бота:

```bash
python bot_server.py
```

6. Отправьте `/start` в Telegram боту и пользуйтесь.

## Развёртывание на Railway

1. Создайте новый проект → **GitHub Repo**.
2. Подключите репозиторий с ботом.
3. Настройте переменные окружения:

   * `TELEGRAM_TOKEN` — токен вашего бота.
   * `DOMAIN` — URL вашего проекта Railway (например `https://mybot.up.railway.app`).
4. Команда запуска:

```bash
python bot_server.py
```

## Структура проекта

```
telegram-pdf-bot/
│
├─ bot_server.py       # основной код бота
├─ pdf_to_text.py      # конвертер PDF → текст
├─ requirements.txt    # зависимости
└─ README.md           # документация
```

## Лицензия

Этот проект доступен под лицензией **CC BY-NC 4.0** — некоммерческое использование. Подробнее смотрите в файле `LICENSE`.

---

> Наслаждайтесь использованием бота и делитесь обратной связью!
