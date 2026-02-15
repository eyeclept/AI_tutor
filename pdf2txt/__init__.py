"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    pdf package
    Contains modules for PDF processing
"""
from .pdf2text import load_pdf_config, pdf_to_text
from .pdf_parser import load_parser_config, split_pdf_by_pages

__all__ = [
    "load_pdf_config",
    "pdf_to_text",
    "load_parser_config",
    "split_pdf_by_pages"
]
