#!/usr/bin/env python3
"""
Script to remove all emojis from Python files and replace with ASCII equivalents
"""
import re

def remove_emojis_from_file(filepath):
    """Remove emojis from a Python file"""
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define emoji replacements
    replacements = {
        '🚨': '[!]',
        '📋': '[PLAN]',
        '🧠': '[AI]',
        '⚡': '[ACT]',
        '📊': '[REPORT]',
        '📈': '[METRICS]',
        '📜': '[LOGS]',
        '🚀': '[DEPLOY]',
        '🔥': '[CRITICAL]',
        '⚠️': '[WARN]',
        '✓': '[OK]',
        '🆕': '[NEW]',
        '🎯': '[TARGET]',
        '🔍': '[SEARCH]',
        '🔄': '[REFRESH]',
    }
    
    # Replace each emoji
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Processed {filepath}")

if __name__ == "__main__":
    remove_emojis_from_file("main.py")
    remove_emojis_from_file("log_analyzer.py")
    print("[OK] All emojis removed successfully!")
