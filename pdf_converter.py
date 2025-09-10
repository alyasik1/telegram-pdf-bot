import pdfplumber
import os

def convert_pdf_to_text(pdf_path):
    txt_path = pdf_path.replace(".pdf", ".txt")
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return txt_path
