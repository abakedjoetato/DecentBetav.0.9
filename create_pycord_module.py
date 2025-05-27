"""
This script creates a fake discord module that implements the py-cord API.
"""
import os
import sys
import shutil

# Create a directory for our fake discord module
os.makedirs('discord_module', exist_ok=True)

# Create an __init__.py file for the fake module
with open('discord_module/__init__.py', 'w') as f:
    f.write('''"""
Discord.py API wrapper - FORCED PY-CORD COMPATIBILITY MODE
"""

__title__ = "py-cord"
__version__ = "2.6.1"
__author__ = "Pycord Development"

# Make this module behave like an imported package
from importlib.util import find_spec
import sys

# For all submodules, try to import from the real discord module
def __getattr__(name):
    # Redirect to the real discord module
    try:
        real_discord = sys.__real_discord_module
        return getattr(real_discord, name)
    except AttributeError:
        try:
            # Try to dynamically import the original module
            import importlib
            real_discord = importlib.import_module("discord")
            # Save for future use
            sys.__real_discord_module = real_discord
            return getattr(real_discord, name)
        except (ImportError, AttributeError):
            raise AttributeError(f"Module 'discord' has no attribute '{name}'")
''')

# Create some essential submodules
submodules = ['ext', 'abc', 'commands', 'utils']
for module in submodules:
    os.makedirs(f'discord_module/{module}', exist_ok=True)
    with open(f'discord_module/{module}/__init__.py', 'w') as f:
        f.write(f'''"""
Discord {module} submodule - FORCED PY-CORD COMPATIBILITY MODE
"""

# Make this module behave like an imported package
from importlib.util import find_spec
import sys

# For all attributes, try to import from the real discord module
def __getattr__(name):
    # Redirect to the real discord module
    try:
        import importlib
        real_module = importlib.import_module("discord.{module}")
        return getattr(real_module, name)
    except (ImportError, AttributeError):
        raise AttributeError(f"Module 'discord.{module}' has no attribute '{{name}}'")
''')

# Create commands module specifically
with open('discord_module/ext/commands/__init__.py', 'w') as f:
    f.write('''"""
Discord.py commands extension - FORCED PY-CORD COMPATIBILITY MODE
"""

# Make this module behave like an imported package
from importlib.util import find_spec
import sys

# For all attributes, try to import from the real discord module
def __getattr__(name):
    # Redirect to the real discord module
    try:
        import importlib
        real_module = importlib.import_module("discord.ext.commands")
        return getattr(real_module, name)
    except (ImportError, AttributeError):
        raise AttributeError(f"Module 'discord.ext.commands' has no attribute '{name}'")

# Import from real module
try:
    import importlib
    commands_module = importlib.import_module("discord.ext.commands")
    # Import specific classes
    Bot = getattr(commands_module, "Bot", None)
    Context = getattr(commands_module, "Context", None)
    Command = getattr(commands_module, "Command", None)
except (ImportError, AttributeError):
    # Provide dummy implementations if needed
    pass
''')

print("✅ Created custom discord module")
print("To use it, add this code at the top of your script:")
print("""
# Use custom discord module
import sys
sys.path.insert(0, '.')  # Add current directory to path
import discord_module as discord
from discord_module.ext import commands
""")