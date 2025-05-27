#!/usr/bin/env python3
"""
Wrapper script to run the Discord bot with proper library configuration
"""

import sys
import subprocess
import importlib.util

def check_py_cord_installation():
    """Check if py-cord is properly installed"""
    try:
        # Try to import discord module
        import discord
        print(f"Found Discord module version: {discord.__version__}")
        
        # Try to import commands from discord.ext
        try:
            from discord.ext import commands
            print("Successfully imported discord.ext.commands")
            return True
        except ImportError:
            print("ERROR: discord.ext.commands not found. This indicates you have discord.py instead of py-cord")
            return False
    except ImportError:
        print("ERROR: discord module not found")
        return False

def install_py_cord():
    """Attempt to install py-cord properly"""
    print("Attempting to install py-cord...")
    try:
        # Uninstall any existing discord packages
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "discord.py", "discord", "py-cord"])
        
        # Install py-cord specifically
        subprocess.check_call([sys.executable, "-m", "pip", "install", "py-cord==2.6.1"])
        
        print("Successfully installed py-cord")
        return True
    except Exception as e:
        print(f"Error installing py-cord: {e}")
        return False

def main():
    """Main function to run the bot"""
    # First, check if py-cord is installed correctly
    if not check_py_cord_installation():
        # Try to install py-cord
        if not install_py_cord():
            print("Failed to install py-cord. Please install it manually.")
            sys.exit(1)
        
        # Verify installation worked
        if not check_py_cord_installation():
            print("Failed to configure py-cord correctly. Please fix manually.")
            sys.exit(1)
    
    # If we get here, py-cord is installed correctly, so run the main bot script
    print("Starting Discord bot...")
    try:
        # Enable more verbose logging
        print("Setting up detailed logging...")
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Import and run the main module
        print("Importing main module...")
        import main
        print("Main module imported successfully")
    except Exception as e:
        print(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()