from pdfminer.high_level import extract_text
import os

def pdf_to_text(file_path, output_path):
    text = extract_text(file_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return output_path
