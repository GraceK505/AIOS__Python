#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions for AIOS
"""

import os
import hashlib
from datetime import datetime

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{units[i]}"

def get_file_icon(filename: str) -> str:
    """Get icon for file type"""
    ext = os.path.splitext(filename)[1].lower()
    
    icons = {
        '.txt': '📄', '.py': '🐍', '.js': '📜', '.html': '🌐',
        '.css': '🎨', '.json': '📋', '.xml': '📄', '.csv': '📊',
        '.md': '📝', '.pdf': '📕', '.jpg': '🖼️', '.png': '🖼️',
        '.gif': '🖼️', '.mp3': '🎵', '.mp4': '🎬', '.zip': '📦',
        '.exe': '⚙️', '.dll': '🔧'
    }
    
    return icons.get(ext, '📄')

def calculate_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file"""
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return ""
    
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return ""