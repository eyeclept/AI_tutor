"""
Author: Richard Baldwin
Date:   2026
Email:  eyeclept@pm.me

Description:
Centralized configuration loader for the project.
"""

from configparser import ConfigParser
import os

_config = None

def load_config(config_file="config.ini"):
    """
    Input:      config_file (str) - path to config.ini
    Output:     ConfigParser object
    Details:    Reads the config file once and caches it for reuse.
    """
    global _config
    if _config is None:
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file '{config_file}' not found.")

        # Enable inline comments
        _config = ConfigParser(
            inline_comment_prefixes=("#", ";")
        )

        _config.read(config_file)

    return _config

def get_section(section_name, config_file="config.ini"):
    """
    Input:      section_name (str)
                config_file (str)
    Output:     dict with keys/values from the section
    Details:    Returns a dictionary of options in the given section
    """
    config = load_config(config_file)
    if section_name not in config:
        raise ValueError(f"Section '{section_name}' not found in config.")
    return dict(config[section_name])
def load_processing_config(config_file="config.ini"):
    """

    Input:      ConfigParser object
    Output:     processing sub object as a dictionary
    Details:    Reads the [processing] section from config.ini and returns it as a dictionary.
    """
    return get_section("processing", config_file)