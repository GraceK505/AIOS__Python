#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System monitor widget for AIOS
"""

import tkinter as tk
from tkinter import ttk
import config

class SystemMonitor(tk.LabelFrame):
    """System monitor with progress bars"""
    
    def __init__(self, parent):
        self.theme = config.THEMES[config.GUI_CONFIG["theme"]]
        
        super().__init__(parent, text="SYSTEM MONITOR",
                        font=(config.GUI_CONFIG["font_family"],
                              config.GUI_CONFIG["title_size"], "bold"),
                        fg=self.theme["accent_green"],
                        bg=self.theme["bg_secondary"],
                        labelanchor="n")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create monitor widgets"""
        content = tk.Frame(self, bg=self.theme["bg_secondary"])
        content.pack(fill="x", padx=10, pady=10)
        
        # CPU
        cpu_frame = tk.Frame(content, bg=self.theme["bg_secondary"])
        cpu_frame.pack(fill="x", pady=5)
        
        tk.Label(cpu_frame, text="CPU:",
                font=(config.GUI_CONFIG["font_family"], 9),
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_secondary"]).pack(side="left")
        
        self.cpu_var = tk.IntVar()
        self.cpu_bar = ttk.Progressbar(cpu_frame, variable=self.cpu_var,
                                      maximum=100, length=200)
        self.cpu_bar.pack(side="left", padx=5)
        
        self.cpu_label = tk.Label(cpu_frame, text="0%",
                                 font=(config.GUI_CONFIG["font_family"], 9),
                                 fg=self.theme["accent_green"],
                                 bg=self.theme["bg_secondary"])
        self.cpu_label.pack(side="left")
        
        # Memory
        mem_frame = tk.Frame(content, bg=self.theme["bg_secondary"])
        mem_frame.pack(fill="x", pady=5)
        
        tk.Label(mem_frame, text="RAM:",
                font=(config.GUI_CONFIG["font_family"], 9),
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_secondary"]).pack(side="left")
        
        self.mem_var = tk.IntVar()
        self.mem_bar = ttk.Progressbar(mem_frame, variable=self.mem_var,
                                      maximum=100, length=200)
        self.mem_bar.pack(side="left", padx=5)
        
        self.mem_label = tk.Label(mem_frame, text="0%",
                                 font=(config.GUI_CONFIG["font_family"], 9),
                                 fg=self.theme["accent_blue"],
                                 bg=self.theme["bg_secondary"])
        self.mem_label.pack(side="left")
        
        # Disk
        disk_frame = tk.Frame(content, bg=self.theme["bg_secondary"])
        disk_frame.pack(fill="x", pady=5)
        
        tk.Label(disk_frame, text="DISK:",
                font=(config.GUI_CONFIG["font_family"], 9),
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_secondary"]).pack(side="left")
        
        self.disk_var = tk.IntVar()
        self.disk_bar = ttk.Progressbar(disk_frame, variable=self.disk_var,
                                       maximum=100, length=200)
        self.disk_bar.pack(side="left", padx=5)
        
        self.disk_label = tk.Label(disk_frame, text="0%",
                                  font=(config.GUI_CONFIG["font_family"], 9),
                                  fg=self.theme["accent_purple"],
                                  bg=self.theme["bg_secondary"])
        self.disk_label.pack(side="left")
        
        # Alert label
        self.alert_label = tk.Label(content, text="",
                                   font=(config.GUI_CONFIG["font_family"], 9),
                                   fg=self.theme["warning"],
                                   bg=self.theme["bg_secondary"])
        self.alert_label.pack(pady=(10, 0))
    
    def update(self, data):
        """Update monitor with new data"""
        try:
            # CPU
            cpu_percent = data["cpu"].get("percent", 0)
            self.cpu_var.set(cpu_percent)
            self.cpu_label.config(text=f"{cpu_percent:.1f}%")
            
            # Memory
            mem_percent = data["memory"].get("percent", 0)
            self.mem_var.set(mem_percent)
            mem_mb = data["memory"].get("used_mb", 0)
            self.mem_label.config(text=f"{mem_percent:.1f}% ({mem_mb}MB)")
            
            # Disk
            disk_percent = data["disk"].get("percent", 0)
            self.disk_var.set(disk_percent)
            self.disk_label.config(text=f"{disk_percent:.1f}%")
            
            # Alerts
            alerts = data.get("alerts", [])
            if alerts:
                self.alert_label.config(text=alerts[0])
            else:
                self.alert_label.config(text="")
                
        except Exception as e:
            print(f"Error updating monitor: {e}")