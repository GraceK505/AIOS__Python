#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget Factory for AIOS
"""

import tkinter as tk
from tkinter import ttk
import config

class WidgetFactory:
    """Factory to create and manage widgets"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.active_widgets = {}
        self.theme = config.THEMES[config.GUI_CONFIG["theme"]]
    
    def create_widget(self, widget_type, **kwargs):
        """Create and return a widget frame"""
        if widget_type == "terminal":
            return self._create_terminal_widget(**kwargs)
        elif widget_type == "info":
            return self._create_info_widget(**kwargs)
        elif widget_type == "screensaver":
            return self._create_screensaver_widget(**kwargs)
        else:
            return self._create_default_widget(widget_type, **kwargs)
    
    def _create_terminal_widget(self, **kwargs):
        """Create a terminal widget"""
        frame = tk.Frame(kwargs.get("parent"), bg=self.theme["bg_secondary"])
        
        # Terminal text area
        text_widget = tk.Text(frame, 
                             height=kwargs.get("height", 15),
                             width=kwargs.get("width", 60),
                             bg=self.theme["bg_text"],
                             fg=self.theme["text_main"])
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Store reference
        if "name" in kwargs:
            self.active_widgets[kwargs["name"]] = frame
        
        return frame
    
    def _create_info_widget(self, **kwargs):
        """Create an info display widget"""
        frame = tk.Frame(kwargs.get("parent"), bg=self.theme["bg_secondary"])
        
        info_text = kwargs.get("text", "Information Widget")
        
        label = tk.Label(frame, 
                        text=info_text,
                        bg=self.theme["bg_secondary"],
                        fg=self.theme["text_main"])
        label.pack(pady=20)
        
        # Store reference
        if "name" in kwargs:
            self.active_widgets[kwargs["name"]] = frame
        
        return frame
    
    def _create_screensaver_widget(self, **kwargs):
        """Create a screensaver widget"""
        frame = tk.Frame(kwargs.get("parent"), bg="black")
        
        # Simple animated text
        canvas = tk.Canvas(frame, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        text_id = canvas.create_text(
            kwargs.get("width", 400) // 2,
            kwargs.get("height", 300) // 2,
            text="AIOS",
            fill="green",
            font=("Courier", 48)
        )
        
        # Store reference
        if "name" in kwargs:
            self.active_widgets[kwargs["name"]] = frame
        
        return frame
    
    def _create_default_widget(self, widget_type, **kwargs):
        """Create a default widget"""
        frame = tk.Frame(kwargs.get("parent"), bg=self.theme["bg_secondary"])
        
        label = tk.Label(frame, 
                        text=f"{widget_type} Widget",
                        bg=self.theme["bg_secondary"],
                        fg=self.theme["text_main"])
        label.pack(pady=20)
        
        # Store reference
        if "name" in kwargs:
            self.active_widgets[kwargs["name"]] = frame
        
        return frame
    
    def close_widget(self, widget_name):
        """Close a specific widget"""
        if widget_name in self.active_widgets:
            self.active_widgets[widget_name].destroy()
            del self.active_widgets[widget_name]
    
    def close_all(self):
        """Close all widgets"""
        for widget in self.active_widgets.values():
            widget.destroy()
        self.active_widgets.clear()