#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration settings for AIOS
"""

# Application Configuration
APP_CONFIG = {
    "name": "AIOS - Artificial Intelligence Operating System",
    "version": "4.0",
    "author": "AIOS Developer",
    "description": "Modular AI Operating System with GUI",
}

# System Configuration
SYSTEM_CONFIG = {
    "update_interval": 2.0,
    "max_processes": 8,
    "cpu_warning": 80.0,
    "memory_warning": 85.0,
    "disk_warning": 90.0,
}

# File System Configuration
FILESYSTEM_CONFIG = {
    "workspace": "aios_workspace",
    "max_file_size": 10485760,  # 10MB
    "backup_enabled": True,
    "backup_count": 5,
    "auto_refresh": True,
    "refresh_interval": 5.0,
}

# GUI Configuration
GUI_CONFIG = {
    "window_size": "1200x700",
    "min_size": "800x600",
    "theme": "dark",
    "font_family": "Consolas",
    "font_size": 10,
    "title_size": 12,
    "monitor_size": 24,
}

# Theme Configuration
THEMES = {
    "dark": {
        "bg_main": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_widget": "#0f3460",
        "bg_text": "#0d1b2a",
        "bg_selected": "#2a2a4a",
        "bg_header": "#0d1021",
        "text_main": "#e0e0e0",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "text_header": "#ffffff",
        "text_highlight": "#ffcc00",
        "accent_blue": "#4cc9f0",
        "accent_green": "#4ade80",
        "accent_red": "#f87171",
        "success": "#6a9955",
        "warning": "#fbbf24",
        "accent_yellow": "#fbbf24",
        "accent_purple": "#a78bfa"
    },
    "light": {
        "bg_main": "#f8f9fa",
        "bg_secondary": "#e9ecef",
        "bg_widget": "#dee2e6",
        "bg_text": "#ffffff",
        "bg_selected": "#ced4da",
        "bg_header": "#343a40",
        "text_main": "#212529",
        "text_primary": "#000000",
        "text_secondary": "#6c757d",
        "text_header": "#ffffff",
        "text_highlight": "#1971c2",
        "accent_blue": "#1e88e5",
        "accent_green": "#43a047",
        "accent_red": "#e53935",
        "success": "#107c10",
        "warning": "#fbbf24",
        "accent_yellow": "#ffb300",
        "accent_purple": "#8e24aa"
    },
    "cyberpunk": {
        "bg_main": "#0a0a0f",
        "bg_secondary": "#151520",
        "bg_widget": "#1e1e2e",
        "bg_text": "#0f0f1a",
        "bg_selected": "#2a2a3e",
        "bg_header": "#0f0f1a",
        "text_main": "#00ff9d",
        "text_primary": "#ffffff",
        "text_secondary": "#00cc7a",
        "text_header": "#ffffff",
        "text_highlight": "#ff00ff",
        "accent_blue": "#00d9ff",
        "accent_green": "#00ff9d",
        "accent_red": "#ff0055",
        "accent_yellow": "#ffff00",
        "accent_purple": "#9d00ff"
    },
}

# Command Configuration
COMMAND_CONFIG = {
    "history_size": 50,
    "auto_complete": True,
    "max_suggestions": 5,
    "response_delay": 0.1,
}

# Future Features Configuration
FUTURE_CONFIG = {
    "enable_voice": False,      # Voice commands
    "enable_3d": False,         # 3D file preview
    "enable_gestures": False,   # Gesture control
    "enable_ai_learning": True, # AI command learning
}