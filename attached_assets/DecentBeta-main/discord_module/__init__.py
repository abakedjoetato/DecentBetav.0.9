"""
Discord.py API wrapper - FORCED PY-CORD COMPATIBILITY MODE
"""

__title__ = "py-cord"
__version__ = "2.6.1"
__author__ = "Pycord Development"

# Make this module behave like an imported package
from importlib.util import find_spec
import sys

# For all submodules, try to import from the real discord module
def __getattr__(name):
    # Redirect to the real discord module
    try:
        real_discord = sys.__real_discord_module
        return getattr(real_discord, name)
    except AttributeError:
        try:
            # Try to dynamically import the original module
            import importlib
            real_discord = importlib.import_module("discord")
            # Save for future use
            sys.__real_discord_module = real_discord
            return getattr(real_discord, name)
        except (ImportError, AttributeError):
            raise AttributeError(f"Module 'discord' has no attribute '{name}'")
