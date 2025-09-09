import PyPDF2
import os

def convert_pdf_to_txt(file_path: str, output_path: str):
    """
    Конвертирует PDF в текстовый файл.
    """
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(text)

    return output_path
 