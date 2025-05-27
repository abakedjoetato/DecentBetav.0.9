"""
Discord utils submodule - FORCED PY-CORD COMPATIBILITY MODE
"""

# Make this module behave like an imported package
from importlib.util import find_spec
import sys

# For all attributes, try to import from the real discord module
def __getattr__(name):
    # Redirect to the real discord module
    try:
        import importlib
        real_module = importlib.import_module("discord.utils")
        return getattr(real_module, name)
    except (ImportError, AttributeError):
        raise AttributeError(f"Module 'discord.utils' has no attribute '{name}'")
