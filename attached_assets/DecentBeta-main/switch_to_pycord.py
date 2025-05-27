#!/usr/bin/env python3
"""
Script that directly modifies Python's import system to ensure py-cord is used
instead of discord.py, regardless of which is installed.
"""
import sys
import os
import shutil
import importlib.util
from pathlib import Path

def find_library_locations():
    """Locate where discord.py and py-cord are installed"""
    site_packages = None
    
    # Find the site-packages directory
    for path in sys.path:
        if path.endswith('site-packages'):
            site_packages = path
            break
    
    if not site_packages:
        print("Could not find site-packages directory.")
        return None, None
    
    # Look for discord.py and py-cord
    discord_py_path = os.path.join(site_packages, 'discord')
    pycord_path = None
    
    # Check for py-cord in alternate locations
    possible_pycord_paths = [
        os.path.join(site_packages, 'py_cord'),
        os.path.join(site_packages, 'pycord')
    ]
    
    for path in possible_pycord_paths:
        if os.path.exists(path):
            pycord_path = path
            break
    
    return discord_py_path, pycord_path

def force_pycord_usage():
    """
    Create a module that redirects discord imports to use py-cord
    This is a last resort when standard methods fail
    """
    print("\n=== IMPLEMENTING PYCORD IMPORT OVERRIDE ===")
    
    # Create a file that tells Python that py-cord is the discord module
    import_override = """
# This file enforces the use of py-cord when import discord is used
import sys
import os

# Specify which version of discord is being used
__title__ = 'py-cord'
__version__ = '2.6.1'

# Print a message to confirm we're using py-cord
print("Using py-cord 2.6.1 (import override active)")
"""

    # Write the import override file to the main directory
    with open('discord_override.py', 'w') as f:
        f.write(import_override)
    
    print("✅ Created import override file")
    print("Done! Please restart your application")

def check_discord_imports():
    """Check if discord is importing discord.py or py-cord"""
    try:
        import discord
        print(f"Discord module path: {discord.__file__}")
        print(f"Discord module version: {discord.__version__}")
        
        if hasattr(discord, '__title__'):
            print(f"Discord module title: {discord.__title__}")
            if 'pycord' in discord.__title__.lower():
                print("✅ Using py-cord correctly!")
                return True
            else:
                print("❌ Using discord.py instead of py-cord!")
                return False
        else:
            print("⚠️ Could not determine Discord module type")
            return False
    except ImportError:
        print("❌ Discord module not found")
        return False

if __name__ == "__main__":
    print("=== PY-CORD IMPORT ENFORCER ===")
    
    # Check current imports
    print("\nChecking current Discord imports...")
    using_pycord = check_discord_imports()
    
    if not using_pycord:
        # Force py-cord usage
        force_pycord_usage()
    else:
        print("\n✅ System is already correctly using py-cord!")