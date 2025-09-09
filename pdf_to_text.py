import os
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract

# Путь к Tesseract (устанавливается на сервере Railway)
TESSERACT_CMD = os.getenv("TESSETACT_CMD", "tesseract")

def pdf_to_txt(file_path: str, output_path: str):
    """
    Конвертация PDF в текст.
    Поддерживает текстовые PDF через pdfminer.
    Для сканированных PDF использует OCR.
    """
    try:
        # Попытка обычного текста
        text = extract_text(file_path)
        if len(text.strip()) > 10:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        # Если пусто, делаем OCR
        pages = convert_from_path(file_path)
        full_text = ""
        for page in pages:
            full_text += pytesseract.image_to_string(page, lang='rus+eng')
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        return True
    except Exception as e:
        print("Ошибка конвертации PDF:", e)
        return False