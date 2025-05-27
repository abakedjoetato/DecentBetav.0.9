#!/usr/bin/env python3
"""
This script fixes the Discord module import paths to ensure py-cord works correctly.
It's meant to be run before starting the main Discord bot.
"""

import sys
import os
import importlib
import site
from pathlib import Path

def find_discord_modules():
    """Find all locations where discord modules might be installed"""
    possible_paths = []
    
    # Check all site packages
    for path in site.getsitepackages():
        discord_path = Path(path) / "discord"
        if discord_path.exists():
            possible_paths.append(str(discord_path.parent))
    
    # Check user site packages
    user_site = site.getusersitepackages()
    discord_user_path = Path(user_site) / "discord"
    if discord_user_path.exists():
        possible_paths.append(str(discord_user_path.parent))
    
    # Check current working directory and subdirectories
    for root, dirs, files in os.walk("."):
        if "discord" in dirs:
            discord_path = Path(root) / "discord"
            if discord_path.exists():
                possible_paths.append(str(discord_path.parent))
    
    return possible_paths

def check_is_pycord(path):
    """Check if the discord module at path is py-cord"""
    try:
        # Try to find a unique py-cord identifier
        init_file = Path(path) / "discord" / "__init__.py"
        if init_file.exists():
            with open(init_file, "r") as f:
                content = f.read()
                if "py-cord" in content.lower():
                    return True
        
        # Check for specific py-cord modules
        application_commands_file = Path(path) / "discord" / "ext" / "commands" / "slash_core.py"
        if application_commands_file.exists():
            return True
            
        return False
    except Exception:
        return False

def add_pycord_path_to_front():
    """Find py-cord and add it to the front of sys.path"""
    paths = find_discord_modules()
    for path in paths:
        if check_is_pycord(path):
            print(f"Found py-cord at {path}")
            
            # Add the py-cord path to the front of sys.path
            if path in sys.path:
                sys.path.remove(path)
            
            sys.path.insert(0, path)
            
            # Force reload the discord module
            if "discord" in sys.modules:
                del sys.modules["discord"]
                print("Removed discord from sys.modules for fresh import")
            
            if "discord.ext" in sys.modules:
                del sys.modules["discord.ext"]
                print("Removed discord.ext from sys.modules for fresh import")
                
            return True
    
    return False

if __name__ == "__main__":
    success = add_pycord_path_to_front()
    if success:
        print("Successfully configured py-cord path")
        
        # Verify import works
        try:
            import discord
            from discord.ext import commands
            print(f"Successfully imported discord (version: {discord.__version__})")
            print(f"Successfully imported commands")
        except ImportError as e:
            print(f"Error importing: {e}")
    else:
        print("Could not find py-cord installation")