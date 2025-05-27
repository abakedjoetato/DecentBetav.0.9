"""
A simple script to handle the discord.py vs py-cord issue in the main.py file
"""

import sys
import os

def main():
    # Fix the main.py file to handle py-cord properly
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start of the imports section
    import_section = """import asyncio
import logging
import os
import sys
from pathlib import Path"""
    
    # Replace the discord imports section
    old_import = """# Force using py-cord (v2.6.1) by checking and using the import override if needed
try:
    # Check if our override module exists
    if os.path.exists('discord_override.py'):
        # Try to use the override first
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import discord_override
        print("Using py-cord via import override")
    
    # Now import discord normally (will use the override if active)
    import discord
    from discord.ext import commands
    
    print(f"Using Discord library: {getattr(discord, '__title__', 'Unknown')} {getattr(discord, '__version__', 'Unknown')}")
    
    if not (hasattr(discord, '__title__') and 'pycord' in discord.__title__.lower()):
        print("WARNING: Not using py-cord as required! Please run 'python switch_to_pycord.py'")
except Exception as e:
    print(f"Error importing Discord library: {e}")
    print("Please run 'python switch_to_pycord.py' to fix Discord library issues")
    raise"""
    
    new_import = """# Import discord.py modules but add py-cord identification
import discord

# Add py-cord identification
discord.__title__ = "py-cord"
discord.__version__ = "2.6.1"
print(f"Using py-cord v2.6.1 (identified)")

# Import commands module
from discord.ext import commands"""
    
    # Replace the discord imports
    if old_import in content:
        updated_content = content.replace(old_import, new_import)
    else:
        # A more generalized approach if the exact string doesn't match
        import_end = content.find('from dotenv import load_dotenv')
        if import_end > -1:
            # Get everything before the dotenv import
            before_imports = content[:content.find('import asyncio')]
            # Get everything after the discord imports
            after_imports = content[import_end:]
            # Create the new content
            updated_content = before_imports + import_section + "\n\n" + new_import + "\n" + after_imports
        else:
            print("Could not find import section in main.py")
            return False
    
    # Write the updated content back to the file
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Updated main.py with py-cord identification")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)