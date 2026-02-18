"""
Author: Richard Baldwin
Date:   2026
Email: eyeclept@pm.me

Description:
ask_ollama package
Contains modules for summarizing text files using Ollama LLM

"""
#imports

from .askOllama import (
    load_llm_config,
    summarize_individual,
    summarize_summaries
)

__all__ = ["load_ollama_config", "summarize_individual", "summarize_summaries"]
