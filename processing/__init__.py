"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    pdf package
    Contains modules for PDF processing
"""
from .pdf2text import load_pdf_config, pdf_to_text, pdf_to_markdown, merge_md_files
from .pdf_parser import load_parser_config, split_pdf, process_pdfs

__all__ = [
    "load_pdf_config",
    "pdf_to_text",
    "load_parser_config",
    "split_pdf",
    "process_pdfs",
    "pdf_to_markdown",
    "merge_md_files"
]
