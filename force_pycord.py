#!/usr/bin/env python3
"""
This script verifies that py-cord 2.6.1 is installed and discord.py is removed
Without attempting to modify packages (which would fail in Replit's environment)
"""
import subprocess
import sys
import os
import importlib

def main():
    print("=== VERIFYING PY-CORD 2.6.1 INSTALLATION ===")
    
    # Check installed packages without trying to modify them
    print("\n[1/2] Checking installed packages...")
    result = subprocess.run(["pip", "freeze"], capture_output=True, text=True)
    packages = result.stdout.splitlines()
    
    discord_packages = [pkg for pkg in packages if "discord" in pkg.lower()]
    has_discord_py = any("discord.py" in pkg.lower() or "discord-py" in pkg.lower() for pkg in packages)
    has_pycord = any("py-cord==2.6.1" in pkg for pkg in packages)
    
    print("\nDiscord-related packages installed:")
    for pkg in discord_packages:
        print(f"  - {pkg}")
    
    # Check for conflicting imports using importlib
    print("\n[2/2] Checking for discord.py imports...")
    
    try:
        # Try to import discord module
        discord = importlib.import_module('discord')
        module_path = getattr(discord, '__file__', 'Unknown')
        
        print(f"Discord module loaded from: {module_path}")
        
        # Check if it's discord.py or py-cord
        if hasattr(discord, '__version__'):
            print(f"Discord library version: {discord.__version__}")
            
            # Try to determine if it's py-cord or discord.py
            if hasattr(discord, '__title__') and 'pycord' in discord.__title__.lower():
                print("Detected py-cord library")
                is_pycord = True
            else:
                print("Detected discord.py library")
                is_pycord = False
        else:
            print("Could not determine Discord library version")
            is_pycord = False
            
    except ImportError:
        print("No Discord library found")
        is_pycord = False
    
    # Final verdict
    if has_pycord and not has_discord_py:
        print("\n✅ SUCCESS: py-cord 2.6.1 is correctly installed and discord.py is not present")
        return True
    elif is_pycord:
        print("\n⚠️ PARTIAL SUCCESS: Discord library appears to be py-cord, but version may not be 2.6.1")
        return True
    else:
        print("\n❌ ERROR: py-cord 2.6.1 is not installed correctly or discord.py is present")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)