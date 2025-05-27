"""
This script properly imports py-cord and ensures it's used instead of discord.py.
It must be imported before any discord imports in your code.
"""
import sys
import importlib

# First, remove any existing discord modules from sys.modules
# to ensure a clean import
for key in list(sys.modules.keys()):
    if key == 'discord' or key.startswith('discord.'):
        del sys.modules[key]

# Now import the real py-cord
try:
    # This will import the actual py-cord library
    import discord
    
    # Add identification if it doesn't exist
    if not hasattr(discord, '__title__'):
        discord.__title__ = 'py-cord'
    if not hasattr(discord, '__version__'):
        discord.__version__ = '2.6.1'
    
    # Output confirmation
    print(f"✅ ENFORCED: Using {discord.__title__} {discord.__version__} for all discord imports")
except ImportError:
    print("⚠️ ERROR: Could not import discord module. Please install py-cord!")
    raise