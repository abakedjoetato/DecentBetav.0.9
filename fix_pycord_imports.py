"""
Comprehensive fix for py-cord 2.6.1 imports across all bot files
This script will fix all Discord imports to use the correct py-cord syntax
"""

import os
import re

def fix_file_imports(file_path):
    """Fix py-cord imports in a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix slash command decorators
        content = re.sub(r'@commands\.slash_command', '@discord.slash_command', content)
        content = re.sub(r'@discord\.ext\.commands\.slash_command', '@discord.slash_command', content)
        
        # Fix command groups
        content = re.sub(r'discord\.ext\.commands\.SlashCommandGroup', 'discord.SlashCommandGroup', content)
        
        # Fix context types
        content = re.sub(r'discord\.ext\.commands\.ApplicationContext', 'discord.ApplicationContext', content)
        
        # Fix option decorators
        content = re.sub(r'@discord\.ext\.commands\.option', '@discord.option', content)
        
        # Fix permission decorators
        content = re.sub(r'@commands\.has_permissions', '@discord.default_permissions', content)
        
        # Fix autocomplete context
        content = re.sub(r'discord\.ext\.commands\.AutocompleteContext', 'discord.AutocompleteContext', content)
        
        # Fix option choices
        content = re.sub(r'discord\.ext\.commands\.OptionChoice', 'discord.OptionChoice', content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"ℹ️ No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all py-cord imports in bot files"""
    files_to_fix = [
        'bot/cogs/core.py',
        'bot/cogs/linking.py', 
        'bot/cogs/stats.py',
        'bot/cogs/leaderboards.py',
        'bot/cogs/bounties.py',
        'bot/cogs/factions.py',
        'bot/cogs/premium.py',
        'bot/cogs/admin_channels.py',
        'bot/cogs/embed_test.py',
        'bot/cogs/economy.py',
        'bot/cogs/gambling.py',
        'bot/cogs/autocomplete.py'
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_file_imports(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print(f"\n🎉 Import fix complete! Fixed {fixed_count} files.")

if __name__ == '__main__':
    main()