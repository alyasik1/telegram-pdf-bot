from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Отправить PDF", callback_data="send_pdf")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)
