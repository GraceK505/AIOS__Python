#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console widget for AIOS
"""

import tkinter as tk
from tkinter import ttk
import config

class Console(tk.LabelFrame):
    """AI console with command history"""
    
    def __init__(self, parent, app):
        self.app = app
        self.theme = config.THEMES[config.GUI_CONFIG["theme"]]
        
        super().__init__(parent, text="AI CONSOLE",
                        font=(config.GUI_CONFIG["font_family"],
                              config.GUI_CONFIG["title_size"], "bold"),
                        fg=self.theme["accent_yellow"],
                        bg=self.theme["bg_secondary"],
                        labelanchor="n")
        
        self.command_history = []
        self.history_index = -1
        self.create_widgets()
        self.setup_tags()
    
    def create_widgets(self):
        """Create console widgets"""
        # Console output
        output_frame = tk.Frame(self, bg=self.theme["bg_widget"])
        output_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Text widget
        self.text = tk.Text(output_frame,
                           bg=self.theme["bg_widget"],
                           fg=self.theme["text_primary"],
                           font=(config.GUI_CONFIG["font_family"],
                                 config.GUI_CONFIG["font_size"]),
                           yscrollcommand=scrollbar.set,
                           wrap="word",
                           relief="flat",
                           borderwidth=0)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text.yview)
        self.text.config(state="disabled")
        
        # Command entry
        entry_frame = tk.Frame(self, bg=self.theme["bg_secondary"])
        entry_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Label(entry_frame, text=">>",
                font=(config.GUI_CONFIG["font_family"], 11, "bold"),
                fg=self.theme["accent_yellow"],
                bg=self.theme["bg_secondary"]).pack(side="left", padx=(0, 5))
        
        self.cmd_var = tk.StringVar()
        self.cmd_entry = tk.Entry(entry_frame,
                                 textvariable=self.cmd_var,
                                 bg=self.theme["bg_widget"],
                                 fg=self.theme["text_primary"],
                                 font=(config.GUI_CONFIG["font_family"], 11),
                                 relief="flat",
                                 insertbackground=self.theme["text_primary"])
        self.cmd_entry.pack(side="left", fill="x", expand=True, ipady=3)
        
        # Send button
        tk.Button(entry_frame, text="Send",
                 command=self.send_command,
                 bg=self.theme["accent_green"],
                 fg="white",
                 relief="flat").pack(side="right", padx=(5, 0))
        
        # Bindings
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        self.cmd_entry.bind("<Up>", self.history_up)
        self.cmd_entry.bind("<Down>", self.history_down)
        self.cmd_entry.focus_set()
    
    def setup_tags(self):
        """Setup text tags for styling"""
        self.text.tag_config("command", foreground=self.theme["accent_yellow"])
        self.text.tag_config("error", foreground=self.theme["accent_red"])
        self.text.tag_config("success", foreground=self.theme["success"])
        self.text.tag_config("info", foreground=self.theme["accent_blue"])
        self.text.tag_config("warning", foreground=self.theme["warning"])
    
    def write(self, text, tag=None):
        """Write text to console"""
        self.text.config(state="normal")
        
        if tag:
            self.text.insert("end", text, tag)
        else:
            self.text.insert("end", text)
        
        self.text.see("end")
        self.text.config(state="disabled")
    
    def clear(self):
        """Clear console"""
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")
    
    def send_command(self):
        """Send command to AI"""
        cmd = self.cmd_var.get().strip()
        if not cmd:
            return
        
        # Add to history
        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        self.cmd_var.set("")
        
        # Execute command
        self.app.execute_command(cmd)
    
    def history_up(self, event):
        """Navigate command history up"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.cmd_var.set(self.command_history[self.history_index])
        return "break"
    
    def history_down(self, event):
        """Navigate command history down"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.cmd_var.set(self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.cmd_var.set("")
        return "break"