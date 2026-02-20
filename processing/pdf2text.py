"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    Converts PDFs into text files preserving folder structure.
    Uses configuration from config.ini.
"""
import fitz  # PyMuPDF
import os
import re
import sys
from utils.config_utils import load_processing_config


def load_pdf_config(config_file="config.ini"):
    """
    Input:      config_file (str)
    Output:     tuple (input_pdf, split_output_dir, text_output_dir)
    Details:    Returns:
                    - input_pdf: path to PDF file or folder
                    - split_output_dir: folder to store split PDFs
                    - text_output_dir: folder to store extracted text
    """
    pdf_cfg = load_processing_config(config_file)

    input_pdf = pdf_cfg.get("input_pdf_dir")
    if not input_pdf:
        raise ValueError("input_pdf must be set in [processing] section of config.ini")

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
                # Get info from filename
                base_part, split_type, page_number = parse_pdf_filename(filename)

                # Extract text
                extracted_text = extract_text_from_pdf(pdf_path)

                if not extracted_text:
                    print(f"----- No selectable text in {pdf_path}")
                    continue

                # Preserve folder structure
                text_dir = get_text_output_dir(output_root, base_part, dirpath, input_root)

                text_filename = os.path.splitext(filename)[0] + ".txt"
                text_path = os.path.join(text_dir, text_filename)

                # Create header line for the top of the file
                header_line = f"<-- {split_type} {page_number} of {base_part} -->\n\n"

                # Write to file
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(header_line)
                    f.write("\n\n".join(extracted_text))  # write the rest of the PDF text

                print(f"Converted: {pdf_path} -> {text_path}")

    print("All PDFs converted to text (images ignored).")
    
def parse_pdf_filename(filename: str):
    """
    Input:      filename (str) - PDF filename, expected format <base>_<split_type>-<number>.pdf
    Output:     tuple (base_part, split_type, page_number)
    Details:    Extracts:
                    - base_part: base file name
                    - split_type: type of split (page, chunk, etc.)
                    - page_number: page or chunk number
                Falls back to defaults if filename doesn't match expected pattern.
    """
    base_name, _ = os.path.splitext(filename)
    if "_" in base_name and "-" in base_name:
        base_part, split_part = base_name.rsplit("_", 1)  # split off last underscore
        split_type, page_number = split_part.split("-", 1)
    else:
        base_part = base_name
        split_type = "unknown"
        page_number = "-1"
    return base_part, split_type, page_number

def extract_text_from_pdf(pdf_path: str):
    """
    Input:      pdf_path (str) - path to a PDF file
    Output:     list of str - text from each page
    Details:    Uses PyMuPDF to extract plain text from all pages.
                Returns an empty list if no selectable text found.
    """
    extracted_text = []
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text")
        if page_text:
            extracted_text.append(page_text.strip())
    return extracted_text

def get_text_output_dir(output_root: str, base_part: str, dirpath: str, input_root: str):
    """
    Input:
        output_root (str) - root folder for text output
        base_part (str)   - base filename to create subfolder for
        dirpath (str)     - current directory path of the PDF
        input_root (str)  - root input folder
    Output:
        str - full path to the folder where the text file should be saved
    Details:
        Preserves folder structure relative to input_root, but nests it under a folder named after base_part.
        Creates the folder if it does not exist.
    """
    relative_path = os.path.relpath(dirpath, input_root)
    text_dir = os.path.join(output_root, base_part, relative_path)
    os.makedirs(text_dir, exist_ok=True)
    return text_dir

def pdf_to_markdown(input_root: str, output_root: str = None, image_root: str = None):
    """
    Input: 
        input_root (str)  - folder containing PDFs
        output_root (str) - folder to store .md files; defaults to text_output_dir from config
        image_root (str)  - folder to store extracted images; defaults to ./images in output_root
    Output: None
    Details:
        Walks input_root, extracts text and images from PDFs using PyMuPDF, writes Markdown files
        preserving folder structure and adding headers for split type/page info.
        Basic formatting (bold, italic, headings, lists) is preserved where possible.
    """
    # Setup output folders
    if not output_root:
        _, _, output_root = load_pdf_config()
    os.makedirs(output_root, exist_ok=True)

    if not image_root:
        image_root = os.path.join(output_root, "images")
    os.makedirs(image_root, exist_ok=True)
    # count all pdf files
    # count all PDFs first
    pdf_files = {}
    for dirpath, _, filenames in os.walk(input_root):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files[filename] = dirpath

    total_pdfs = len(pdf_files)
    processed = 0
    # walk through all pdfs in input_root
    for filename, dirpath in pdf_files.items():
        pdf_path = os.path.join(dirpath, filename)
        # extract filename info
        base_part, split_type, page_number = parse_pdf_filename(filename)

        # Open PDF and extract structured text & images
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Error opening PDF {pdf_path}: {e}")

            processed += 1
            print_progress_bar(processed, total_pdfs)
            continue

        md_lines = []
        seen_xrefs = set()  # prevent duplicate image extraction

        for page_idx, page in enumerate(doc, start=1):
            # Extract text blocks (dict) to detect formatting
            try:
                blocks = page.get_text("dict")["blocks"]
            except Exception as e:
                print(f"Error extracting page {page_idx} from {pdf_path}: {e}")
                continue
            for b in blocks:
                if b["type"] == 0:  # text block
                    md_lines.extend(process_text_block(b))

            # Extract images
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]

                # avoid saving duplicates
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)

                md_lines.extend(
                    process_image_xref(
                        doc,
                        xref,
                        page_idx,
                        base_part,
                        image_root,
                        output_root,
                    )
                )


        if not md_lines:
            print(f"----- No selectable text or images in {pdf_path}")
            continue

        # Preserve folder structure
        md_dir = get_text_output_dir(output_root, base_part, dirpath, input_root)
        md_filename = os.path.splitext(filename)[0] + ".md"
        md_path = os.path.join(md_dir, md_filename)

        # Header line
        header_line = f"<-- {split_type} {page_number} of {base_part} -->\n\n"

        # Write Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(header_line)
            f.write("\n\n".join(md_lines))

        processed += 1
        print_progress_bar(processed, total_pdfs)
        

    print("All PDFs converted to Markdown with images.")

def process_text_block(block: dict) -> list[str]:
    """
    Converts a PyMuPDF text block into Markdown lines.
    Preserves basic formatting (bold, italic) and simple headings based on font size.
    
    Input:
        block (dict) - a PyMuPDF block with type==0
    Output:
        List of Markdown lines extracted from the block
    """
    raw_lines = []
    md_lines = []
    # extract lines
    for line in block["lines"]:
        line_text = ""
        for span in line["spans"]:
            text = span.get("text", "").strip()
            if not text:
                continue
            # Formatting
            if span.get("flags", 0) & 2:  # bold
                text = f"**{text}**"
            if span.get("flags", 0) & 1:  # italic
                text = f"*{text}*"
            line_text += text
        if not line_text:
            continue
        # table of contents merge logic

        
        # Heading detection
        size = line["spans"][0]["size"]
        if size >= 16:
            raw_lines.append(f"# {line_text}")
        elif size >= 13:
            raw_lines.append(f"## {line_text}")
        else:
            raw_lines.append(line_text)
        # merge numeric only lines (table of content)
        for cur in raw_lines:
            cur_strip = cur.strip()
            # Detect numeric-only content (after removing heading markers)
            numeric_only = re.sub(r'^#+\s*', '', cur_strip).isdigit()
            if numeric_only and md_lines:
                # Attach numeric to previous line (preserve previous heading markers)
                prev = md_lines.pop()
                merged = f"{prev} {cur_strip.split()[-1]}"  # append just the number
                md_lines.append(merged)
            else:
                md_lines.append(cur_strip)


    return md_lines

def process_image_xref(doc, xref: int, page_idx: int, base_part: str, image_root: str, output_root: str) -> list[str]:
    """
    
    Inputs:
        doc: PDF document object
        xref: Image reference
        page_idx: Page index
        base_part: Base part of the file name
        image_root: Directory to save images
        output_root: Directory to save output files
        
    Output:
        List of Markdown lines (image references)
    Details:
        Extracts an image using xref and saves it safely.
    """
    md_lines = []
    try:
        pix = fitz.Pixmap(doc, xref)

        image_name = f"{base_part}_{page_idx}_{xref}.png"
        image_path = os.path.join(image_root, image_name)

        # Convert CMYK/alpha safely
        if pix.n < 5:
            pix.save(image_path)
        else:
            pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(image_path)

        pix = None

        md_lines.append(
            f"![{image_name}]({os.path.relpath(image_path, output_root)})"
        )

    except Exception as e:
        print(f"Error extracting image xref {xref} from page {page_idx}: {e}")

    return md_lines

def merge_md_file(md_file_root, base_dir):
    """
    Input: filepath containing md files
    Output: bool for if file was created
    Details: Placeholder
    """
    # vars
    md_output_path = ""
    # check if file path exits
    # walk through all pdfs in input_root
    for dirpath, _, filenames in os.walk(md_file_root):
        for filename in filenames:
            # check if md
            if filename.lower().endswith(".md"):
                #full path to current md file
                md_page_path = os.path.join(dirpath, filename)
                # extract filename info
                base_part, split_type, page_number = parse_pdf_filename(filename)
                md_output_name = base_part + ".md"
                md_output_path = os.path.join(base_dir, md_output_name)
                #check if output md file exists, if not make it
                if not os.path.exists(md_output_path):                
                    with open(md_output_path, 'w') as f:
                        pass  # empty file created
                #append file contents to output_md
                with open(md_output_path, 'a') as output_md:
                    #open filename and append contents
                    with open(md_page_path, 'r') as input_file:
                        output_md.write(input_file.read())
                        output_md.write("\n\n")  # separate pages
                #TODO this will keep appending if you run the same files again, need to make so it won't repeat
    #check if file was created
    return (md_output_path == True)

def merge_md_files(input_dir):
    """
    Input: input dir where md file folders are
    Output: None
    Details: Placeholder
    """

    for dirpath, dirnames, _ in os.walk(input_dir):
        # for each folder run merge_md_file(md_file_root)
        for dirname in dirnames:
            dir = os.path.join(input_dir, dirname)
            if merge_md_file(dir, input_dir):
                print(f"merged {dirname} to {dir}.md")
    return

def function():
    """
    Input: None
    Output: None
    Details: Placeholder
    """
    return

def print_progress_bar(current, total, bar_length=40):
    """
    Input: 
        current: how many items have been processed
        total: total items to process
        bar_length: number of characters for the bar
    Output: None
    Details: 
    Prints a progress bar in terminal.
    """
    fraction = current / total
    filled_length = int(bar_length * fraction)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)
    percent = fraction * 100
    sys.stdout.write(f"\rProcessing PDFs: |{bar}| {percent:.1f}% ({current}/{total})")
    sys.stdout.flush()