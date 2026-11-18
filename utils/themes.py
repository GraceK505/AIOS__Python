#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Theme management for AIOS
"""

import tkinter as tk
from tkinter import ttk
import config

class ThemeManager:
    """Manage GUI themes"""
    
    def __init__(self):
        self.current = config.GUI_CONFIG["theme"]
        self.themes = config.THEMES
    
    def get_theme(self, name: str = None) -> dict:
        """Get theme by name or current theme"""
        if name and name in self.themes:
            return self.themes[name]
        return self.themes.get(self.current, self.themes["dark"])
    
    def set_theme(self, name: str, root: tk.Tk = None):
        """Set current theme"""
        if name in self.themes:
            self.current = name
            
            if root:
                self.apply_theme(root)
            
            return True
        return False
    
    def apply_theme(self, root: tk.Tk):
        """Apply theme to root window"""
        theme = self.get_theme()
        
        # Apply to root window
        root.configure(bg=theme["bg_main"])
        
        # Update ttk styles
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure button styles for launcher
        style.configure("Launcher.TButton",
                       background=theme["bg_header"],
                       foreground=theme["text_header"],
                       borderwidth=1,
                       relief="raised",
                       padding=8,
                       font=("Arial", 10))
        
        style.map("Launcher.TButton",
                 background=[('active', theme["accent_blue"]),
                            ('pressed', theme["bg_secondary"])],
                 foreground=[('active', "white")])
        
        # Configure menu button style
        style.configure("Launcher.TMenubutton",
                       background=theme["bg_header"],
                       foreground=theme["text_header"],
                       borderwidth=1,
                       relief="raised",
                       padding=8,
                       font=("Arial", 10))
        
        style.map("Launcher.TMenubutton",
                 background=[('active', theme["accent_blue"]),
                            ('pressed', theme["bg_secondary"])],
                 foreground=[('active', "white")])
        
        # Treeview
        style.configure("Treeview",
                       background=theme["bg_widget"],
                       foreground=theme["text_primary"],
                       fieldbackground=theme["bg_widget"],
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=theme["bg_secondary"],
                       foreground=theme["accent_blue"],
                       relief="flat")
        style.map("Treeview",
                 background=[('selected', theme["bg_selected"])])
        
        # Scrollbar
        style.configure("Vertical.TScrollbar",
                       background=theme["bg_secondary"],
                       troughcolor=theme["bg_main"],
                       borderwidth=1)
        
        style.configure("Horizontal.TScrollbar",
                       background=theme["bg_secondary"],
                       troughcolor=theme["bg_main"],
                       borderwidth=1)
        
        # Progressbar
        style.configure("Horizontal.TProgressbar",
                       background=theme["accent_green"],
                       troughcolor=theme["bg_widget"],
                       borderwidth=1)
        
        # Entry and Combobox
        style.configure("TEntry",
                       fieldbackground=theme["bg_text"],
                       foreground=theme["text_main"],
                       insertcolor=theme["text_main"])
        
        style.configure("TCombobox",
                       fieldbackground=theme["bg_text"],
                       foreground=theme["text_main"],
                       background=theme["bg_secondary"])
        
        # Frame border
        style.configure("Border.TFrame",
                       background=theme["accent_blue"],
                       borderwidth=2)
    
    def get_color(self, color_name: str, theme_name: str = None) -> str:
        """Get specific color from theme"""
        theme = self.get_theme(theme_name)
        return theme.get(color_name, "#000000")
    
    def cycle_theme(self, root: tk.Tk = None):
        """Cycle to next theme"""
        theme_names = list(self.themes.keys())
        current_idx = theme_names.index(self.current)
        next_idx = (current_idx + 1) % len(theme_names)
        
        return self.set_theme(theme_names[next_idx], root)
    
    def create_gradient(self, color1: str, color2: str, steps: int = 10) -> list:
        """Create gradient between two colors"""
        import colorsys
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        gradient = []
        for i in range(steps):
            ratio = i / (steps - 1)
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
            gradient.append(rgb_to_hex((r, g, b)))
        
        return gradient
    
    def create_header_gradient(self, theme_name: str = None) -> list:
        """Create gradient for header background"""
        theme = self.get_theme(theme_name)
        return self.create_gradient(theme["bg_header"], theme["bg_secondary"])