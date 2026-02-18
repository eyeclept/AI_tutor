#!/usr/bin/env python3
"""
Author: Richard Baldwin
Date:   2026
Email:  eyeclept@pm.me

Description:
    Main entry point for PDF processing.
    Converts PDFs to text using configuration from config.ini.
    Supports optional PDF splitting and Ollama summarization.
    TODO: add cli options for some options including directories and others
    TODO: make scrub board to keep track of stuff
    TODO: parse PDFs using PyMuPDF to use PDF layout metadata to detect headings
    TODO: optional, use LLM to check pyMuPDF
    TODO: modify askOllama to chunk based on section
    TODO: when extracting text, keep track of page number using a map possible 
            (need to make work with the saving to file functionality)
    TODO: Chunk based on page number to allow for searching content
    TODO: add functionality to generate quizzes (with keys) and flashcards
    TODO: stretch goal: integrate it to custom LLM where the LLM acts as a teacher for the book
    TODO: integrate with RAG
    TODO: add more controls in ini
    TODO: set up cli
    TODO: set up basic webui
    TODO: refactor file traversal to have a "get all of these files" function thet gets a list of all files with checks and what not
            and then use that list for processing
    TODO: add a way to specify which files to process in the ini file
    TODO: make it so you can specify multiple input folders (and output folders)
    TODO: make it so you can specify multiple output folders (and input folders)

"""

from processing import (
    load_pdf_config,
    pdf_to_text,
    load_parser_config,
    split_pdf_by_pages
)
from llm import load_llm_config, summarize_individual, summarize_summaries
import os


def process_pdfs(input_root, output_root, split_pages):
    """
    Step 3: Process PDFs
    Input:
        input_root (str) - folder containing original PDFs
        output_root (str) - folder to save extracted text
        split_pages (list of int) - pages to split PDFs at
    Output: None
    Details:
        - If split_pages are defined, split PDFs first
        - Convert PDFs (or split PDFs) to text
    """
    os.makedirs(output_root, exist_ok=True)

    if split_pages:
        if os.path.isfile(input_root):
            # Just one PDF
            split_pdf_by_pages(input_root, output_root, split_pages)
        elif os.path.isdir(input_root):
            for dirpath, _, filenames in os.walk(input_root):
                for filename in filenames:
                    if filename.lower().endswith(".pdf"):
                        pdf_path = os.path.join(dirpath, filename)
                        split_pdf_by_pages(pdf_path, output_root, split_pages)
        else:
            raise ValueError(f"{input_root} does not exist or is not a folder/file")

def summarize_text_files():
    """
    Step 4: Load Ollama config and summarize text
    Input: None
    Output: None
    Details:
        - Reads Ollama configuration
        - Summarizes individual files if enabled
        - Summarizes combined summaries if enabled
    """
    cfg = load_llm_config()
    if cfg["summarize_individual"]:
        summarize_individual(cfg)
    if cfg["summarize_summaries"]:
        summarize_summaries(cfg)

def main():
    """
    Input: None
    Output: None
    Details:
        Orchestrates PDF conversion and Ollama summarization
    """
    # Step 1: Load PDF config
    input_root, split_output_dir, text_output_dir = load_pdf_config()

    # Step 2: Load parser config (page numbers to split PDF)
    split_pages = load_parser_config()["split_pages"]

    # Step 3: Process PDFs
    process_pdfs(input_root, split_output_dir, split_pages)

    # Step 4: Convert to text
    pdf_to_text(split_output_dir, text_output_dir)

    # Step 4: Summarize text using Ollama
    summarize_text_files()

    print("\nProcessing complete.")


def function():
    """
    Input: None
    Output: None
    Details: Placeholder for future main utilities
    """
    return


if __name__ == "__main__":
    main()
