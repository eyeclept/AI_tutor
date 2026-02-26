"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
    Converts PDFs into text files preserving folder structure.
    Uses configuration from config.ini.
"""
import fitz  # PyMuPDF
import unicodedata
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
    Output:     tuple (base_part, split_type, number)
    Details:    Extracts:
                    - base_part: base file name
                    - split_type: type of split (page, chunk, etc.)
                    - number: page, chunk or etc number
                Falls back to defaults if filename doesn't match expected pattern.
    """
    base_name, _ = os.path.splitext(filename)
    if "_" in base_name and "-" in base_name:
        base_part, split_part = base_name.rsplit("_", 1)  # split off last underscore
        split_type, number = split_part.split("-", 1)
    elif "_" in base_name and not "-" in base_name:
        base_part, split_type = base_name.rsplit("_", 1)  # split off last underscore
        number = "-1"
        split_type = "unknown"
    else:
        base_part = base_name
        split_type = "unknown"
        number = "-1"
    return base_part, split_type, number

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
        image_root (str)  - folder to store extracted images; unused now
    Output: None
    Details:
        Walks input_root, extracts text from PDFs using PyMuPDF, writes Markdown files
        preserving folder structure and adding headers for split type/page info.
        Basic formatting (bold, italic, headings, lists) is preserved where possible.
        Images are ignored.
    """
    # Setup output folders
    if not output_root:
        _, _, output_root = load_pdf_config()
    os.makedirs(output_root, exist_ok=True)

    # count all PDF files
    pdf_files = {}
    for dirpath, _, filenames in os.walk(input_root):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files[filename] = dirpath

    total_pdfs = len(pdf_files)
    processed = 0

    for filename, dirpath in pdf_files.items():
        pdf_path = os.path.join(dirpath, filename)
        base_part, split_type, page_number = parse_pdf_filename(filename)

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Error opening PDF {pdf_path}: {e}")
            processed += 1
            print_progress_bar(processed, total_pdfs)
            continue

        md_lines = []

        for page_idx, page in enumerate(doc, start=1):
            try:
                blocks = page.get_text("dict")["blocks"]
            except Exception as e:
                print(f"Error extracting page {page_idx} from {pdf_path}: {e}")
                continue

            for b in blocks:
                if b["type"] == 0:  # only process text blocks
                    md_lines.extend(process_text_block(b))

            md_lines = merge_consecutive_headers(md_lines)
            md_lines = format_toc(md_lines)

        if not md_lines:
            print(f"----- No selectable text in {pdf_path}")
            continue

        md_dir = get_text_output_dir(output_root, base_part, dirpath, input_root)
        md_filename = os.path.splitext(filename)[0] + ".md"
        md_path = os.path.join(md_dir, md_filename)

        header_line = f"<-- {split_type} {page_number} of {base_part} -->\n\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(header_line)
            f.write("\n\n".join(md_lines))

        processed += 1
        print_progress_bar(processed, total_pdfs)
    fix_pdf_errors(output_root)

    print("All PDFs converted to Markdown without images.")


def process_text_block(block: dict) -> list[str]:
    """
    Converts a PyMuPDF text block into Markdown lines.
    Preserves basic formatting (bold, italic) and simple headings based on font size.
    """
    md_lines = []
    bullet_chars = ["■", "•", "·", "◦"]

    debug = False
    debug_texts = ["should do in such a situation. You know that the costs to your current employer will increase if",
                    "53 (1): 169–196. doi:10.1006/ijhc.2000.0370.",
                    "The aim of this chapter is to introduce system models that may be"]
    for line in block["lines"]:
        line_text = ""

        # --- Extract spans ---
        for span in line["spans"]:
            text = span.get("text", "")
            text = unicodedata.normalize("NFKC", text)

            if not text.strip():
                continue

             # --- DEBUG CHECK ---
            if debug and text.strip() in debug_texts:
                print(f"DEBUG MATCH FOUND: {text}")


            # Formatting
            if span.get("flags", 0) & 2:  # bold
                text = f"**{text}**"
            if span.get("flags", 0) & 1:  # italic
                text = f"*{text}*"

            line_text += text

        line_text = line_text.strip()
        if not line_text:
            continue

        # --- Bullet normalization ---
        for b in bullet_chars:
            if line_text.startswith(b):
                line_text = "- " + line_text[len(b):].lstrip()
                break

        # --- Heading detection ---
        size = line["spans"][0]["size"]
        if size >= 16:
            formatted_line = f"# {line_text}"
        elif size >= 13:
            formatted_line = f"## {line_text}"
        else:
            formatted_line = line_text
        md_lines.append(formatted_line)

    # Merge consecutive headers at the end using the dedicated function
    md_lines = merge_consecutive_headers(md_lines)
    return md_lines

def merge_consecutive_headers(md_lines: list[str], line_range: tuple[int, int] | None = None) -> list[str]:
    """
    Input: None
    Output: None
    Details: Placeholder
    """
    merged_lines = []
    buffer = []

    debug = False
    debug_texts = [
        "## Objectives",
        "# Objectives",
        "Objectives"
    ]

    # Determine range of lines to process
    start_idx = line_range[0] if line_range else 0
    end_idx = line_range[1] if line_range else len(md_lines)

    for i, line in enumerate(md_lines):
        # Lines outside the range are appended as-is
        if i < start_idx or i >= end_idx:
            merged_lines.append(line)
            continue

        # --- DEBUG CHECK ---
        if debug and line.strip() in debug_texts:
            print(f"DEBUG MATCH FOUND: {line.strip()}")

        # Only match headers that start with '#' followed by a space
        if re.match(r'^#\s', line):
            text = line.lstrip('#').strip()
            buffer.append(text)  # Add current header to buffer
        else:
            if buffer:  # Flush buffered headers
                merged_lines.append('# ' + ' '.join(buffer))
                buffer = []
            merged_lines.append(line)

    # Flush any remaining buffered headers at the end of range
    if buffer:
        merged_lines.append('# ' + ' '.join(buffer))

    return merged_lines

def format_toc(md_lines: list[str]) -> list[str]:
    """
    Detects numbered lines (like 1.1, 1.2, etc.) and formats as bullets or indented items.
    Example:
        1.1Professional software development
    Becomes:
        - 1.1 Professional software development
    """
    formatted_lines = []
    for line in md_lines:
        stripped = line.strip()
        # Detect numbered section at start
        match = re.match(r'^(\d+(\.\d+)*)\s*(.*)', stripped)
        if match:
            number = match.group(1)
            text = match.group(3)
            formatted_lines.append(f"- {number} {text}")
        else:
            formatted_lines.append(line)
    return formatted_lines


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

def merge_md_file(md_file_root, merged_name):
    """
    Input: filepath containing md files
    Output: bool for if file was created
    Details: Placeholder
    """
    # vars
    md_output_path = None
    base_part = None

    # First pass: determine output filename from first valid md file
    for dirpath, _, filenames in os.walk(md_file_root):
        for filename in filenames:
            if re.search(r'_page-\d+\.md$', filename, re.IGNORECASE):
                base_part, _, _ = parse_pdf_filename(filename)
                md_output_name = f"{base_part}_{merged_name}.md"
                md_output_path = os.path.join(dirpath, md_output_name)
                break
        if md_output_path:
            break

    if not md_output_path:
        return False  # No markdown files found

    # If merged file already exists, delete it to prevent duplication
    if os.path.exists(md_output_path):
        os.remove(md_output_path)
    
    # get base part
    base_part, _, _ = parse_pdf_filename(filename)

    # Create fresh empty merged file
    with open(md_output_path, 'w', encoding='utf-8') as f:
        pass

    # Second pass: append pages in sorted order
    for dirpath, _, filenames in os.walk(md_file_root):
        for filename in filenames:
            if filename.lower().endswith(".md"):
                md_page_path = os.path.join(dirpath, filename)

                with open(md_page_path, 'r', encoding='utf-8') as input_file:
                    with open(md_output_path, 'a', encoding='utf-8') as output_md:
                        output_md.write(input_file.read())
                        output_md.write("\n\n")  # separate pages

    return os.path.exists(md_output_path)

def merge_md_files(input_dir, merged_name):
    """
    Input: input dir where md file folders are
    Output: None
    Details: Placeholder
    """
    merged_dirs = []  # list to store directories successfully merged

    for dirpath, dirnames, _ in os.walk(input_dir):
        for dirname in dirnames:
            working_dir = os.path.join(input_dir, dirname)
            if merge_md_file(working_dir, merged_name):
                print(f"merged {dirname} to {working_dir}/{dirname}_{merged_name}.md")
                filename = f"{dirname}_{merged_name}.md"
                merged_dirs.append((working_dir, filename))

    return merged_dirs

def split_book_by_chapter(working_dir, filename):
    """
    Input: working_dir (str): Path to dir where merged the filename .md file
           filename (str): Name of the merged markdown file
    Output: None
    Details: Split the merged markdown file into chapters. Ensures splits occur at the start of the line.
    """
    merged_md_path = os.path.join(working_dir, filename)

    if not os.path.exists(merged_md_path):
        raise FileNotFoundError(f"Merged file not found: {merged_md_path}")

    # Extract book name from file name
    base_part, _, _ = parse_pdf_filename(filename)

    # Read merged content line by line
    with open(merged_md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chunks = []
    current_chunk = []

    # Regex pattern: matches 4-line sets (formerly 3) ignoring digit at end of 3rd line, will check 5th line for '##'
    chapter_regex = re.compile(r' -->\n\n# ')

    i = 0
    while i < len(lines):
        if i + 4 < len(lines):  # now looking at 5 lines
            line_set = ''.join(lines[i:i+4])  # first 4 lines for the previous pattern
            fifth_line = lines[i+4].lstrip()
            if chapter_regex.search(line_set) and fifth_line.startswith('##'):
                # Start of new chapter detected, save current chunk
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                current_chunk = []
        current_chunk.append(lines[i])
        i += 1

    # Append the last chunk
    if current_chunk:
        chunks.append(''.join(current_chunk))

    # Write each chunk to its own file
    for idx, chunk_text in enumerate(chunks):
        chapter_number = idx  # chapter0 is pre-chapter content
        output_filename = f"{base_part}_chapter-{chapter_number}.md"
        output_path = os.path.join(working_dir, output_filename)
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(chunk_text)

    print(f"Split into {len(chunks)} chapters.")


def fix_pdf_errors(input_dir: str):
    """
    Input: None
    Output: None
    Details:     Loop through all page markdown files in the input_dir and fix common PDF extraction issues.

    """

    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.lower().endswith(".md"):
                file_path = os.path.join(dirpath, filename)
                fix_title_mislocation(file_path)

def fix_title_mislocation(md_path: str):
    """
    Input: None
    Output: None
    Details: Placeholder
    """
    chapter_end_pattern = re.compile(r'^# ')

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return  # empty file

    last_line = lines[-1].strip()    
    if chapter_end_pattern.match(last_line):
        # Remove the last line (misplaced heading)
        misplaced_heading = lines.pop(-1)

        # Ensure there are two newlines after the heading
        if not misplaced_heading.endswith("\n"):
            misplaced_heading += "\n"
        misplaced_heading += "\n"

        # Insert after the second line (index 2)
        if len(lines) >= 2:
            lines.insert(2, misplaced_heading)
        else:
            lines.append(misplaced_heading)

    # --- Merge consecutive headers after fix ---
    lines = merge_consecutive_headers(lines)

    # --- Ensure each line ends with a newline before writing ---
    for i, line in enumerate(lines):
        if not line.endswith("\n"):
            lines[i] = line + "\n"

    # Overwrite file with corrected content
    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

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