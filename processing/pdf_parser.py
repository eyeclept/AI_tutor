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
import shutil
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

def function():
    """
    Input: None
    Output: None
    Details: Placeholder
    """
    return
def split_pdf(pdf_path, output_dir, split_pages = []):
    """
    Input: 
        pdf_path (str)       - path to the source PDF
        output_dir (str)     - folder to save split PDFs
        split_pages (list) (opt) - 
                            page numbers (1-indexed) to split at
                            e.g., [1, 5, 10] produces chunks:
                            pages 1-4, 5-9, 10-end
    Output: None
    Details: Placeholder for future main utilities
    """
    # Ensure the output folder exists; if not, create it
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(pdf_path)

    total_pages = len(reader.pages)
    split_pages, split_by_page = generate_split_pages(total_pages, split_pages)
    split_pdf_by_pages(pdf_path, output_dir, split_pages, reader, total_pages, split_by_page)
    return
def generate_split_pages(total_pages, split_pages):
    """
    Generates a list of 1-indexed page numbers to split at.

    Input:
        total_pages (int)        - total number of pages in PDF
        custom_splits (list)     - list of page numbers to split at (1-indexed)

    Output:
        List of 1-indexed page numbers to split at
        bool for if pages were split on every page
    """
    if split_pages:
        # Use the provided custom splits
        return split_pages, False
    else:
        # Split after every page: pages 1,2,3,...,total_pages
        print("Splitting by page: total_pages =", total_pages)
        return list(range(1, total_pages + 1)), True

def split_pdf_by_pages(pdf_path, output_dir, split_pages, reader, total_pages, split_by_page = False):
    """
    Splits a PDF into multiple PDFs based on page numbers.

    Input:
        pdf_path (str)       - path to the source PDF
        output_dir (str)     - folder to save split PDFs
        split_pages (list)   - page numbers (1-indexed) to split at
                               e.g., [1, 5, 10] produces chunks:
                               pages 1-4, 5-9, 10-end
                               reader (PdfReader)   - preloaded PdfReader object for the source PDF
                               total_pages (int)    - total number of pages in the PDF
    Output:
        List of file paths for the split PDFs

    Details:
        - Creates the output folder if it doesn't exist
        - Iterates over the split page indices and generates a new PDF for each chunk
        - Uses pdfplumber to read pages and append to new PDF objects
        - Returns a list of paths to all generated PDFs
        TODO: modify to not split, only copy pdf if split_pages is empty
    """
    # vars
    chunk_suffix = "_chunk-"    # Define a variable for the chunk suffix
    if split_by_page:
        chunk_suffix = "_page-"
    split_paths = []            # List to store the output file paths of the split PDFs
    start_idx = 0               # Start index for the first chunk (0-based)
    # check if split_pages is empty, copy pdf if it is
    if not split_pages:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        dest_path = os.path.join(output_dir, f"{base_name}{chunk_suffix}0.pdf")
        shutil.copy2(pdf_path, dest_path)  # copy the file with metadata
        split_paths.append(dest_path)
        return split_paths

    # Create a list of split indices with an "end marker" to include the last chunk
    # Example: split_pages=[1,5,10], total_pages=15 → split_indices=[1,5,10,16]
    # Ensure the last index goes to the end, but only if not already present
    split_indices = split_pages.copy()  # copy to avoid modifying the original list
    if not split_indices or split_indices[-1] != total_pages + 1:
        split_indices.append(total_pages + 1)

    # Iterate over each end page in split_indices
    for i, end_page in enumerate(split_indices):
        # Convert 1-indexed end_page to 0-indexed end_idx, cap at total_pages
        end_idx = min(end_page - 1, total_pages)

        # If start index is already past the last page, stop processing
        if start_idx >= total_pages:
            break

        # Create a new PDF writer object for this chunk
        writer = PdfWriter()

        # Add all pages from start_idx up to (but not including) end_idx
        for page in reader.pages[start_idx:end_idx]:
            writer.add_page(page)

        # Construct the output file path for this chunk
        chunk_path = os.path.join(
            output_dir,
            f"{os.path.splitext(os.path.basename(pdf_path))[0]}{chunk_suffix}{i}.pdf"
        )

        # Write the chunk to disk
        with open(chunk_path, "wb") as f:
            writer.write(f)

        # Add this chunk's path to the list of split paths
        split_paths.append(chunk_path)

        # Update start_idx for the next iteration
        start_idx = end_idx

    # Return the list of all split PDF paths
    return split_paths

def process_pdfs(input_root, output_root, split_pages):
    """
    Step 3: Process PDFs
    Input:
        input_root (str) - folder containing original PDFs
        output_root (str) - folder to save extracted text
        split_pages (dict oflist of int) - pages to split PDFs at
    Output: None
    Details:
        - If split_pages are defined, split PDFs first
        - Convert PDFs (or split PDFs) to text
    """
    pdf_path_list = []
    os.makedirs(output_root, exist_ok=True)
    if os.path.isfile(input_root):
        print("1 PDF to process")
        # Just one PDF
        split_pdf(input_root, output_root, split_pages)
    elif os.path.isdir(input_root):
        for dirpath, _, filenames in os.walk(input_root):
            for filename in filenames:
                if filename.lower().endswith(".pdf"):
                    pdf_path_list.append(os.path.join(dirpath, filename))
        print(f"{len(pdf_path_list)} pdf(s) to process")
        for pdf_path in pdf_path_list:
            split_pdf(pdf_path, output_root, split_pages)
    else:
        raise ValueError(f"{input_root} does not exist or is not a folder/file")