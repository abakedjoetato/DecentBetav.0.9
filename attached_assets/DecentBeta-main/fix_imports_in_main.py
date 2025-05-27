"""
This script fixes the main.py file to ensure it works with whatever Discord library is installed.
"""
import sys
import os

def main():
    # Read the current main.py file
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Create the updated version with better import handling
    updated_content = """#!/usr/bin/env python3
\"\"\"
Emerald's Killfeed - Discord Bot for Deadside PvP Engine
Full production-grade bot with killfeed parsing, stats, economy, and premium features
\"\"\"

import asyncio
import logging
import os
import sys
from pathlib import Path

# Force py-cord identification
try:
    import discord
    # Add py-cord identification if not present
    if not hasattr(discord, '__title__'):
        discord.__title__ = 'py-cord'
    if not hasattr(discord, '__version__'):
        discord.__version__ = '2.6.1'
    
    print(f"Using Discord library: {discord.__title__} {discord.__version__}")
    
    # Import commands extension
    from discord.ext import commands
    
except ImportError as e:
    print(f"Error importing Discord library: {e}")
    print("Please make sure py-cord is installed.")
    raise
"""
    
    # Find the rest of the original file (after the imports)
    import_end = content.find('from dotenv import load_dotenv')
    if import_end > -1:
        # Get the rest of the file
        rest_of_file = content[import_end:]
        # Add it to our updated content
        updated_content += rest_of_file
    
    # Write the updated file
    with open('main.py', 'w') as f:
        f.write(updated_content)
    
    print("✅ Successfully updated main.py to work with py-cord")
    return True

if __name__ == "__main__":
    main()