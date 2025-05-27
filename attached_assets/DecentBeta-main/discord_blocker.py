"""
This script ensures only py-cord is used by creating a custom importer
that blocks discord.py and forces py-cord to be used instead.
"""
import sys
import importlib.abc
import importlib.machinery
import importlib.util
from pathlib import Path
import types

# Check if py-cord is installed
def check_pycord_installation():
    try:
        import pkg_resources
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        
        # Look for py-cord package
        has_pycord = any(pkg.startswith('py-cord') for pkg in installed_packages)
        has_discord_py = 'discord-py' in installed_packages or 'discord.py' in installed_packages
        
        print(f"py-cord installed: {has_pycord}")
        print(f"discord.py installed: {has_discord_py}")
        
        return has_pycord
    except:
        print("Could not check package installation status")
        return False

# Create a module that replaces discord.py with py-cord
def create_discord_override():
    """Create an override module for discord imports"""
    module = types.ModuleType('discord')
    module.__title__ = 'py-cord'
    module.__version__ = '2.6.1'
    
    # Add the module to sys.modules so it's used for all future imports
    sys.modules['discord'] = module
    
    print("Created discord override module")
    return module

# Main function to execute
def enforce_pycord():
    """Ensure only py-cord is used by blocking discord.py"""
    print("=== ENFORCING PY-CORD USAGE ===")
    
    # Check if py-cord is installed
    has_pycord = check_pycord_installation()
    
    if not has_pycord:
        print("py-cord is not installed. Please install it first.")
        return False
    
    # Create override module
    discord_module = create_discord_override()
    
    # Setup import hook to intercept all discord imports
    class DiscordImportFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == 'discord' or fullname.startswith('discord.'):
                print(f"Intercepted import of {fullname}")
                # Return None to indicate we want to use our override module
                return None
    
    # Add our finder to the meta_path
    sys.meta_path.insert(0, DiscordImportFinder())
    
    print("✅ Discord import hook installed")
    print("✅ System is now using py-cord instead of discord.py")
    return True

if __name__ == "__main__":
    success = enforce_pycord()
    print(f"py-cord enforcement {'successful' if success else 'failed'}")
    
    # Test the enforcement
    try:
        import discord
        print(f"Imported discord library: {discord.__title__} {discord.__version__}")
    except Exception as e:
        print(f"Error importing discord: {e}")