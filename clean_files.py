# clean_files.py
import os
import re

def clean_file(filepath):
    """Remove non-ASCII characters from a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Replace common problematic characters
        replacements = {
            '•': '*',      # Bullet to asterisk
            '—': '-',      # Em dash to hyphen
            '–': '-',      # En dash to hyphen
            '"': '"',      # Ensure straight quotes
            "'": "'",
            '`': "'",
            "''": "'",
            '""': '"',
            '\x95': '*',   # Windows bullet character
            '\x96': '-',   # Windows dash
            '\x97': '-',   # Windows dash
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Also remove any remaining non-ASCII characters
        content = content.encode('ascii', 'ignore').decode('ascii')
        
        # Write back with UTF-8 encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Cleaned: {filepath}")
    except Exception as e:
        print(f"✗ Error cleaning {filepath}: {e}")

# Clean all Python files in current directory and subdirectories
current_dir = os.path.dirname(os.path.abspath(__file__))

for root, dirs, files in os.walk(current_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            clean_file(filepath)

print("\n✅ All files cleaned successfully!")