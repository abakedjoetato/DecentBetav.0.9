#!/usr/bin/env python3
"""
Script to ensure py-cord 2.6.1 is installed and discord.py is completely removed
"""
import os
import sys
import subprocess
import pkg_resources

def main():
    """Ensure py-cord 2.6.1 is installed and discord.py is completely removed"""
    print("🛠️ Fixing Discord dependencies...")
    
    # Step 1: Uninstall any discord.py related packages
    print("\n1. Removing any discord.py packages")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "discord", "discord.py", "discord-py"], 
                      check=False, capture_output=True)
        print("✅ Removed discord.py packages")
    except Exception as e:
        print(f"⚠️ Error removing discord.py: {e}")
    
    # Step 2: Install py-cord 2.6.1
    print("\n2. Installing py-cord 2.6.1")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "py-cord==2.6.1"], 
                      check=True, capture_output=True)
        print("✅ Installed py-cord 2.6.1")
    except Exception as e:
        print(f"❌ Failed to install py-cord: {e}")
        return False
    
    # Step 3: Verify installation
    print("\n3. Verifying installation")
    try:
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        
        if "py-cord" in installed_packages:
            print(f"✅ py-cord {installed_packages['py-cord']} is installed")
        elif "discord-py" in installed_packages:
            print(f"⚠️ discord-py {installed_packages['discord-py']} is installed")
            print("❌ Verification failed - discord.py is still installed!")
            return False
        else:
            print("❌ Neither py-cord nor discord.py found!")
            return False
        
        # Import and verify discord module is py-cord
        import importlib
        importlib.invalidate_caches()
        
        # Try importing discord
        import discord
        print(f"✅ Using {getattr(discord, '__title__', 'Unknown')} {getattr(discord, '__version__', 'Unknown')}")
        
        if not (hasattr(discord, '__title__') and 'pycord' in discord.__title__.lower()):
            print("❌ Not using py-cord as required!")
            return False
        
        return True
    
    except ImportError:
        print("❌ Failed to import discord module")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*50)
    if success:
        print("✅ Discord dependencies fixed successfully!")
    else:
        print("❌ Failed to fix Discord dependencies")
    print("="*50)
    sys.exit(0 if success else 1)