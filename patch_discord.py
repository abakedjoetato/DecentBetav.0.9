"""
This script patches the discord module to ensure it's using py-cord.
"""
import os
import sys
import importlib.util
import importlib.machinery
import shutil
from pathlib import Path

def find_site_packages():
    """Find the site-packages directory in Python path"""
    # First check the known location in Replit
    replit_site_packages = "/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"
    if os.path.exists(replit_site_packages):
        return replit_site_packages
    
    # Fall back to searching sys.path
    for p in sys.path:
        if p.endswith('site-packages'):
            return p
    
    return None

def patch_discord_init(discord_path):
    """Add py-cord identification to the discord __init__.py file"""
    init_file = os.path.join(discord_path, '__init__.py')
    
    if not os.path.exists(init_file):
        print(f"Discord __init__.py not found at {init_file}")
        return False
    
    # Read the current file
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we need to patch it
    if '__title__ = "py-cord"' in content:
        print("File already patched with py-cord identifier")
        return True
    
    # Add py-cord identification
    pycord_patch = '''
# Patched by discord fixer
__title__ = "py-cord"
__version__ = "2.6.1"
'''
    
    # Write the patched file
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(pycord_patch + content)
        print("Successfully patched discord/__init__.py")
        return True
    except Exception as e:
        print(f"Failed to patch file: {e}")
        return False

def main():
    print("=== PATCHING DISCORD MODULE TO USE PY-CORD ===")
    
    # Find site-packages
    site_packages = find_site_packages()
    if not site_packages:
        print("Could not find site-packages directory")
        return False
    
    print(f"Found site-packages at: {site_packages}")
    
    # Look for discord module
    discord_path = os.path.join(site_packages, 'discord')
    if not os.path.exists(discord_path):
        print(f"Discord module not found at {discord_path}")
        return False
    
    print(f"Found discord module at: {discord_path}")
    
    # Patch the discord __init__.py file
    success = patch_discord_init(discord_path)
    
    if success:
        print("\n✅ Successfully patched discord module to use py-cord")
        print("Please restart your application for changes to take effect")
    else:
        print("\n❌ Failed to patch discord module")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)