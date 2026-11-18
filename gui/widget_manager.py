#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget Manager for AIOS
"""

import tkinter as tk
from tkinter import ttk
import config

class WidgetManager:
    """Manages widget windows"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.widget_windows = {}
        self.theme = config.THEMES[config.GUI_CONFIG["theme"]]
    
    def open_widget_window(self, widget_name, content_func=None):
        """Open a widget in a separate window"""
        if widget_name in self.widget_windows:
            # Bring to front if already open
            window = self.widget_windows[widget_name]
            window.lift()
            window.focus_force()
            return window
        
        # Create new window
        window = tk.Toplevel(self.parent_app.root)
        window.title(f"AIOS - {widget_name.title()}")
        window.geometry("400x300")
        window.configure(bg=self.theme["bg_main"])
        
        # Position near main window
        x = self.parent_app.root.winfo_x() + 50
        y = self.parent_app.root.winfo_y() + 50
        window.geometry(f"+{x}+{y}")
        
        # Add close button
        close_btn = ttk.Button(window, text="✕",
                              command=lambda: self.close_widget_window(widget_name))
        close_btn.place(x=370, y=5, width=25, height=25)
        
        # Create widget content
        if content_func:
            content = content_func(window)
            if content:
                content.pack(fill="both", expand=True, padx=10, pady=30)
        else:
            # Default content
            label = tk.Label(window, 
                           text=f"{widget_name} Widget",
                           bg=self.theme["bg_main"],
                           fg=self.theme["text_main"])
            label.pack(pady=20)
        
        # Store reference
        self.widget_windows[widget_name] = window
        
        # Bind close event
        window.protocol("WM_DELETE_WINDOW", 
                       lambda: self.close_widget_window(widget_name))
        
        return window
    
    def close_widget_window(self, widget_name):
        """Close a widget window"""
        if widget_name in self.widget_windows:
            self.widget_windows[widget_name].destroy()
            del self.widget_windows[widget_name]
    
    def close_all(self):
        """Close all widget windows"""
        for window in self.widget_windows.values():
            window.destroy()
        self.widget_windows.clear()
    
    def is_open(self, widget_name):
        """Check if widget window is open"""
        return (widget_name in self.widget_windows and 
                self.widget_windows[widget_name].winfo_exists())