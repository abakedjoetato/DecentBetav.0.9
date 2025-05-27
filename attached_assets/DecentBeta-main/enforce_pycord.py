"""
This script enforces the use of py-cord by modifying imports and checking for discord-py usage.
"""
import os
import importlib
import sys

def check_discord_library():
    """Check if we're using py-cord or discord.py"""
    print("Checking Discord library...")
    
    try:
        # Import discord module
        discord = importlib.import_module('discord')
        print(f"Discord module loaded from: {getattr(discord, '__file__', 'Unknown')}")
        
        # Check version and title attributes
        if hasattr(discord, '__version__'):
            print(f"Discord library version: {discord.__version__}")
            
            # Check if it's py-cord
            is_pycord = False
            if hasattr(discord, '__title__'):
                title = discord.__title__
                print(f"Discord library title: {title}")
                is_pycord = 'pycord' in title.lower()
            
            if is_pycord:
                print("✅ USING PY-CORD - This is correct!")
                return True
            else:
                print("❌ USING DISCORD.PY - This needs to be fixed!")
                return False
        else:
            print("⚠️ Could not determine Discord library version")
            return False
            
    except ImportError:
        print("No Discord library found")
        return False

def print_usage_recommendations():
    """Print recommendations for ensuring py-cord usage"""
    print("\n=== PY-CORD USAGE RECOMMENDATIONS ===")
    print("1. Make sure your project only imports py-cord, not discord.py")
    print("2. If you're seeing discord.py being used despite installing py-cord, check:")
    print("   - Your pyproject.toml file (should only list py-cord)")
    print("   - Any requirements.txt files (should only list py-cord)")
    print("3. Use Pycord-specific commands and features, such as:")
    print("   - For slash commands: @bot.slash_command() instead of @bot.command()")
    print("   - For syncing: await bot.sync_commands() or bot.sync_commands()")
    print("4. Remember py-cord and discord.py have API differences")
    
if __name__ == "__main__":
    # Check which Discord library is being used
    using_pycord = check_discord_library()
    
    # Print recommendations if needed
    if not using_pycord:
        print_usage_recommendations()
    
    sys.exit(0 if using_pycord else 1)