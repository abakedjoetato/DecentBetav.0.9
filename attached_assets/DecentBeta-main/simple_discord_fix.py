"""
Simple script to verify which Discord library is being used and ensure it's py-cord.
"""
import importlib.util
import sys
import os

def main():
    print("=== DISCORD LIBRARY CHECK ===")
    
    try:
        # Try to import discord
        import discord
        
        # Get information about the discord module
        discord_path = getattr(discord, '__file__', 'Unknown')
        discord_version = getattr(discord, '__version__', 'Unknown')
        discord_title = getattr(discord, '__title__', 'Unknown')
        
        print(f"Discord module path: {discord_path}")
        print(f"Discord module version: {discord_version}")
        print(f"Discord module title: {discord_title}")
        
        # Check if it's py-cord
        if hasattr(discord, '__title__') and 'pycord' in discord.__title__.lower():
            print("\n✅ SUCCESS: Using py-cord")
            return True
        else:
            print("\n❌ ERROR: Not using py-cord")
            return False
    
    except ImportError:
        print("❌ Discord module not found")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)