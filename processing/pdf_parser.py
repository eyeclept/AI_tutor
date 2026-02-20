"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    PDF splitting utility that reads config from utils.config_utils
    - Reads PDF path, split folder, and split pages from config.ini
    - Splits the PDF into chunks based on page numbers
    - Saves split PDFs to the output folder
"""

import os
import pdfplumber
from pypdf import PdfReader, PdfWriter
from utils.config_utils import load_processing_config


def load_parser_config(config_file="config.ini"):
    """
    Reads PDF splitting configuration from the [pdf] section in config.ini.

    Input:
        config_file (str) - path to the config.ini file
    Output:
        dict containing:
            - input_pdf: str - path to the source PDF
            - split_output_dir: str - folder to save split PDFs
            - split_pages: list of int - page numbers at which to split PDF
    Details:
        - Uses utils.config_utils.get_section to get a dictionary for the [pdf] section
        - Converts comma-separated split_pages string into a list of integers
        - Provides a default output folder if none is specified
    """
    # Get the [pdf] section as a dictionary
    pdf_cfg = load_processing_config(config_file)

    # Path to the PDF to split
    input_pdf = pdf_cfg.get("input_pdf_dir")

    # Output folder for split PDFs (default to ./pdf_split_output if not specified)
    split_output_dir = pdf_cfg.get("split_output_dir", "./pdf_split_output")

    # Pages at which to split, as a list of integers
    split_pages_str = pdf_cfg.get("split_pages", "")
    split_pages = [int(p.strip()) for p in split_pages_str.split(",")] if split_pages_str else []

    # Return configuration as a dictionary
    return {
        "input_pdf": input_pdf,
        "split_output_dir": split_output_dir,
        "split_pages": split_pages
    }


def split_pdf_by_pages(pdf_path, output_dir, split_pages):
    """
    Splits a PDF into multiple PDFs based on page numbers.

    Input:
        pdf_path (str)       - path to the source PDF
        output_dir (str)     - folder to save split PDFs
        split_pages (list)   - page numbers (1-indexed) to split at
                               e.g., [1, 5, 10] produces chunks:
                               pages 1-4, 5-9, 10-end
    Output:
        List of file paths for the split PDFs

    Details:
        - Creates the output folder if it doesn't exist
        - Iterates over the split page indices and generates a new PDF for each chunk
        - Uses pdfplumber to read pages and append to new PDF objects
        - Returns a list of paths to all generated PDFs
        TODO: modify to not split, only copy pdf if split_pages is empty
    """
    os.makedirs(output_dir, exist_ok=True)
    split_paths = []

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    split_indices = split_pages + [total_pages + 1]  # Add end marker
    start_idx = 0

    for i, end_page in enumerate(split_indices):
        end_idx = min(end_page - 1, total_pages)
        if start_idx >= total_pages:
            break

        writer = PdfWriter()
        for page in reader.pages[start_idx:end_idx]:
            writer.add_page(page)

        chunk_path = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(pdf_path))[0]}_chunk{i}.pdf"
        )
        with open(chunk_path, "wb") as f:
            writer.write(f)

        split_paths.append(chunk_path)
        start_idx = end_idx

    return split_paths