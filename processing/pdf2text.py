"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    Converts PDFs into text files preserving folder structure.
    Uses configuration from config.ini.
"""

import os
import pdfplumber
from utils.config_utils import get_section


def load_pdf_config(config_file="config.ini"):
    """
    Input:      config_file (str)
    Output:     tuple (input_pdf, split_output_dir, text_output_dir)
    Details:    Returns:
                    - input_pdf: path to PDF file or folder
                    - split_output_dir: folder to store split PDFs
                    - text_output_dir: folder to store extracted text
    """
    pdf_cfg = get_section("pdf", config_file)

    input_pdf = pdf_cfg.get("input_pdf")
    if not input_pdf:
        raise ValueError("input_pdf must be set in [pdf] section of config.ini")

    split_output_dir = pdf_cfg.get("split_output_dir", "./pdf_split_output")
    text_output_dir = pdf_cfg.get("text_output_dir", "./pdf_text_output")

    return input_pdf, split_output_dir, text_output_dir


def pdf_to_text(input_root: str, output_root: str = None):
    """
    Input: 
        input_root (str)  - folder containing PDFs
        output_root (str) - folder to store .txt files; defaults to text_output_dir from config
    Output: None
    Details:
        Walks input_root, extracts text from PDFs, writes text files preserving folder structure
    """
    # If output_root is None, read from config
    if not output_root:
        _, _, output_root = load_pdf_config()

    os.makedirs(output_root, exist_ok=True)

    for dirpath, _, filenames in os.walk(input_root):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(dirpath, filename)
                extracted_text = []

                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text.append(page_text)

                if not extracted_text:
                    print(f"⚠️ No selectable text in {pdf_path}")
                    continue

                # Preserve folder structure
                relative_path = os.path.relpath(dirpath, input_root)
                text_dir = os.path.join(output_root, relative_path)
                os.makedirs(text_dir, exist_ok=True)

                text_filename = os.path.splitext(filename)[0] + ".txt"
                text_path = os.path.join(text_dir, text_filename)

                with open(text_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(extracted_text))

                print(f"Converted: {pdf_path} -> {text_path}")

    print("All PDFs converted to text (images ignored).")
