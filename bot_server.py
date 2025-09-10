import os
import aiofiles
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from PyPDF2 import PdfReader

# Токен берем из переменных Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Папка для временных файлов
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 📌 Главное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📄 Отправить PDF", callback_data="send_pdf")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


# 📌 Приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — *PDF → TXT бот*.\n\n"
        "📌 Я могу конвертировать PDF в текстовый файл.\n\n"
        "Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# 📌 Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "send_pdf":
        await query.edit_message_text(
            "📤 Отправьте PDF-файл (до *200 МБ*), и я сконвертирую его в текст."
        )
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ *Инструкция:*\n\n"
            "1️⃣ Нажмите «📄 Отправить PDF»\n"
            "2️⃣ Загрузите PDF до 200 МБ\n"
            "3️⃣ Получите обратно текстовый файл `.txt`\n\n"
            "👉 Очень удобно для чтения больших документов.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )


# 📌 Сохранение и конвертация PDF
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document

    # Проверяем формат
    if not file.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Пожалуйста, отправьте именно *PDF* файл.", parse_mode="Markdown")
        return

    # Ограничение размера
    if file.file_size > 200 * 1024 * 1024:
        await update.message.reply_text("⚠️ Файл слишком большой. Максимум *200 МБ*.", parse_mode="Markdown")
        return

    await update.message.reply_text("📥 Загружаю файл...")

    # Сохраняем PDF
    new_file = await context.bot.get_file(file.file_id)
    file_path = os.path.join(UPLOAD_DIR, file.file_name)

    async with aiofiles.open(file_path, "wb") as f:
        await new_file.download_to_memory(out=f)

    await update.message.reply_text("🔄 Конвертирую PDF в текст...")

    # Конвертация
    try:
        text_file_path = file_path.replace(".pdf", ".txt")

        reader = PdfReader(file_path)
        extracted_text = []

        for page in reader.pages:
            extracted_text.append(page.extract_text() or "")

        async with aiofiles.open(text_file_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(extracted_text))

        # Отправляем текстовый файл
        async with aiofiles.open(text_file_path, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=os.path.basename(text_file_path)),
                caption="✅ Конвертация завершена! Вот ваш текст:"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обработке PDF: {e}")

    finally:
        # Чистим временные файлы
        try:
            os.remove(file_path)
            os.remove(text_file_path)
        except Exception:
            pass


# 📌 Главная функция
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()


if __name__ == "__main__":
    main()
