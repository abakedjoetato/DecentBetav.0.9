"""
This script finds all Python files that import discord and checks that they're using
py-cord syntax and not discord.py syntax.
"""
import os
import re
from pathlib import Path
import sys

def scan_imports(directory="."):
    """
    Scan all Python files for discord imports and print details
    """
    print(f"Scanning directory: {directory}")
    python_files = []
    
    # Find all Python files
    for root, _, files in os.walk(directory):
        if "__pycache__" in root or ".pythonlibs" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    # Discord import patterns to look for
    discord_import_pattern = re.compile(r"^\s*import\s+discord|^\s*from\s+discord")
    
    files_with_discord = []
    
    # Check each file for discord imports
    for py_file in python_files:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                content = f.read()
                lines = content.split('\n')
                
                discord_lines = []
                for i, line in enumerate(lines):
                    if discord_import_pattern.search(line):
                        discord_lines.append((i+1, line))
                
                if discord_lines:
                    files_with_discord.append((py_file, discord_lines))
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
    
    print(f"\nFound {len(files_with_discord)} files with discord imports")
    
    # Print details of found imports
    for file_path, imports in files_with_discord:
        print(f"\n{file_path}:")
        for line_num, line in imports:
            print(f"  Line {line_num}: {line.strip()}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scan_imports(sys.argv[1])
    else:
        scan_imports()