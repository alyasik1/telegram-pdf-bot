import os

# TOKEN теперь берется напрямую из переменных окружения Railway
TOKEN = os.environ.get("TOK")  # Здесь "TOK" — имя переменной, которое вы задали в Railway

# Если токен по какой-то причине не задан
if not TOKEN:
    raise ValueError("❌ Переменная окружения 'TOK' не найдена! Задайте токен в Railway.")
