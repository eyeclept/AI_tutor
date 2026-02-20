"""
Author: Richard Baldwin
Date:   2026
Email:  eyeclept@pm.me

Description:
    Module for summarizing text files using Ollama LLM.
    Config-driven, supports summarizing individual files and combined summaries.
"""
import re
import os
import sys
import textwrap
import ollama
# Add project root to sys.path so sibling packages can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from utils.config_utils import get_section

def load_llm_config(config_file="config.ini"):
    """
    Input:      config_file (str) - path to config.ini
    Output:     dict - configuration values for ollama module
    Details:    pulls required info from the config file
    """
    llm_cfg = get_section("llm", config_file)

    folders_str = llm_cfg.get("folders", "")
    folders = [f.strip() for f in folders_str.split(",") if f.strip()]



    return {
        "folders": folders,
        "model_name": llm_cfg.get("model_name"),
        "chunk_size": int(llm_cfg.get("chunk_size", 0)),
        "line_width": int(llm_cfg.get("line_width", 80)),
        "summary_folder": llm_cfg.get("summary_folder"),

        # safer boolean parsing
        "summarize_individual": llm_cfg.get("summarize_individual", "false").lower() == "true",
        "summarize_summaries": llm_cfg.get("summarize_summaries", "false").lower() == "true",

        # prompt fields
        "summary_chunk_pp": llm_cfg.get("summary_chunk_pp", ""),
        "summary_refinement_pp": llm_cfg.get("summary_refinement_pp", ""),
        # New structured chunk options
        "chunk_llm_options": {
            "temperature": float(llm_cfg.get("chunk_temperature", 0.2)),
            "top_p": float(llm_cfg.get("chunk_top_p", 0.9)),
            "num_predict": int(llm_cfg.get("chunk_num_predict", 3072)),
            "num_ctx": int(llm_cfg.get("chunk_num_ctx", 32768)),
        },
        # Refinement summarization options
        "refine_llm_options": {
            "temperature": float(llm_cfg.get("refine_temperature", 0.1)),
            "top_p": float(llm_cfg.get("refine_top_p", 0.9)),
            "num_predict": int(llm_cfg.get("refine_num_predict", 4096)),
            "num_ctx": int(llm_cfg.get("refine_num_ctx", 32768)),
        }
    }

def get_text_files(folders):
    """
    Input:      folder_paths (list of str) - folders to search
    Output:     list of text file paths
    Details:    gets text files to feed into ollama
    """
    text_files = []
    # Ensure we are looping over each folder
    for folder in folders:
        # Skip if folder is None or empty
        if not folder:
            continue

        # Walk the folder
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.lower().endswith(".txt"):
                    text_files.append(os.path.join(dirpath, filename))

    return text_files
def chunk_text(text, max_chars, overlap=500):
    """
    Input:      text (str), max_chars (int)
    Output:     list of text chunks
    Details:    chunks text to specific size for ollama
    Sentence-aware chunking with overlap.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            # Add overlap from end of previous chunk
            overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
            current_chunk = overlap_text + sentence + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def summarize_text(text, model, cfg):
    """
    Input:      text (str), model (str), chunk_size (int), line_width (int), summary_chunk_pp (str)
    Output:     summarized and wrapped text (str)
    Details:    has ollama summerize text
    TODO: add debug flag that saves intermediate summaries
    TODO: move ollama.generate options to config.ini
    """
    #vars
    #cfg vars
    model_name = cfg["model_name"]
    chunk_size = cfg["chunk_size"]
    line_width = cfg["line_width"]
    summary_refinement_pp = cfg["summary_refinement_pp"]
    summary_chunk_pp = cfg["summary_chunk_pp"]
    chunk_options = cfg["chunk_llm_options"]
    refine_options = cfg["refine_llm_options"]
    #other vars
    chunks = chunk_text(text, chunk_size, overlap=500)
    summarized_chunks = []

    for i, chunk in enumerate(chunks, start=1):
        prompt = f"{summary_chunk_pp}\n\n{chunk}"
        try:
            response = ollama.generate(
                model=model_name,
                prompt=prompt,
                options=chunk_options
            )
        except Exception as e:
            print(f"Error summarizing chunk {i}: {e}")
            continue

        summary_text = response["response"]
        summarized_chunks.append(summary_text)
        print(f"  Chunk {i}/{len(chunks)} summarized.")

    # Combine summaries
    combined_summary = "\n\n".join(summarized_chunks)

    # refinement pass
    refine_prompt = summary_refinement_pp + "\n\n" + combined_summary
    try:
        response = ollama.generate(
            model=model,
            prompt=refine_prompt,
            options=refine_options
        )
    except Exception as e:
        print(f"Error Combining Chunks {e}")
    final_summary = response["response"]

    wrapped_summary = "\n".join(textwrap.wrap(final_summary, width=line_width))
    return wrapped_summary

def estimate_tokens(text):
    """
    Input:      None
    Output:     None
    Details:    
    """
    return len(text.split()) * 1.3

def save_summary(text, filename, summary_folder):
    """
    Input:      text (str), filename (str), summary_folder (str)
    Output:     path to saved summary (str)
    Details:    saves summary to file in summary folder
    """
    os.makedirs(summary_folder, exist_ok=True)
    path = os.path.join(summary_folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Summary saved to '{path}'")
    return path
def summarize_individual(cfg):
    """
    Input:      None
    Output:     None
    Details:    
    """

    # vars
    folders = cfg["folders"]
    summary_folder = cfg["summary_folder"]
    # Get all text files
    text_files = get_text_files(folders)
    print(f"Found {len(text_files)} text files.")
    # Summarize individual files
    for file_path in text_files:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        print(f"\nProcessing '{file_path}'...")
        final_summary = summarize_text(text, cfg)

        base_filename = os.path.basename(file_path)
        summary_filename = base_filename.replace(".txt", "_summary.txt")
        save_summary(final_summary, summary_filename, summary_folder)


def summarize_summaries(cfg):
    """
    Input:      None
    Output:     None
    Details:    disabled for later refactoring
    """
    return
    model_name = cfg["model_name"]
    chunk_size = cfg["chunk_size"]
    line_width = cfg["line_width"]
    summary_folder = cfg["summary_folder"]
    summary_chunk_pp = cfg["summary_chunk_pp"]
    summary_refinement_pp = cfg["summary_refinement_pp"]

    # Summarize all summaries together
    summary_files = [
        os.path.join(summary_folder, f)
        for f in os.listdir(summary_folder)
        if f.endswith("_summary.txt")
    ]

    if not summary_files:
        print("No summary files found to combine.")
        return
    
    combined_text_parts = []

    for file_path in summary_files:
        base_filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        combined_text_parts.append(f"--- {base_filename} ---\n{content}\n")

    combined_text = "\n".join(combined_text_parts)
    all_summaries_path = save_summary(combined_text, "ALL_SUMMARIES.txt", summary_folder)

    print("\nGenerating final summary of ALL_SUMMARIES.txt...")
    with open(all_summaries_path, "r", encoding="utf-8") as f:
        all_text = f.read()

    combined_prompt = (
        "Combine the following individual summaries into one coherent narrative. "
        "Remove repetitive introductions and make the text flow naturally as a single summary:\n\n"
    )

    final_summary_text = summarize_text(all_text, model_name, chunk_size, line_width, combined_prompt, summary_refinement_pp)
    save_summary(final_summary_text, "ALL_SUMMARIES_FINAL.txt", summary_folder)


# ------------------- Placeholder Function -------------------

def function():
    """
    Input:      None
    Output:     None
    Details:    
    """
    return
