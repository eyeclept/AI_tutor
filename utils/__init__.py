"""
utils/__init__.py
Utility package for shared helpers across the project
"""

# Import the config utility so it can be accessed as utils.load_config, etc.
from .config_utils import load_config, get_section

__all__ = ["load_config", "get_section"]
