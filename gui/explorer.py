#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File explorer widget for AIOS
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import config

class FileExplorer(tk.Frame):
    """File explorer with navigation"""
    
    def __init__(self, parent, filesystem, app):
        super().__init__(parent)
        self.fs = filesystem
        self.app = app
        self.theme = config.THEMES[config.GUI_CONFIG["theme"]]
        self.configure(bg=self.theme["bg_secondary"])
        self.create_widgets()
    
    def create_widgets(self):
        """Create explorer widgets"""
        # Title
        tk.Label(self, text="FILE EXPLORER", 
                font=(config.GUI_CONFIG["font_family"], 
                      config.GUI_CONFIG["title_size"], "bold"),
                fg=self.theme["accent_purple"],
                bg=self.theme["bg_secondary"]).pack(pady=(10, 5))
        
        # Navigation buttons
        nav_frame = tk.Frame(self, bg=self.theme["bg_secondary"])
        nav_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.back_btn = tk.Button(nav_frame, text="← Back", 
                                 command=self.go_back,
                                 bg=self.theme["bg_widget"],
                                 fg=self.theme["text_primary"],
                                 relief="flat")
        self.back_btn.pack(side="left", padx=2)
        
        self.forward_btn = tk.Button(nav_frame, text="Forward →",
                                    command=self.go_forward,
                                    bg=self.theme["bg_widget"],
                                    fg=self.theme["text_primary"],
                                    relief="flat")
        self.forward_btn.pack(side="left", padx=2)
        
        tk.Button(nav_frame, text="↻ Refresh",
                 command=self.refresh,
                 bg=self.theme["accent_blue"],
                 fg="white",
                 relief="flat").pack(side="right", padx=2)
        
        # Current directory
        dir_frame = tk.Frame(self, bg=self.theme["bg_widget"])
        dir_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(dir_frame, text="Location:",
                font=(config.GUI_CONFIG["font_family"], 9),
                fg=self.theme["text_secondary"],
                bg=self.theme["bg_widget"]).pack(side="left", padx=(5, 2))
        
        self.dir_label = tk.Label(dir_frame, text="",
                                 font=(config.GUI_CONFIG["font_family"], 9, "bold"),
                                 fg=self.theme["accent_yellow"],
                                 bg=self.theme["bg_widget"])
        self.dir_label.pack(side="left", fill="x", expand=True)
        
        # File list with treeview
        tree_frame = tk.Frame(self, bg=self.theme["bg_widget"])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, columns=("Size", "Type", "Modified"),
                                show="tree headings", height=15)
        
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                       background=self.theme["bg_widget"],
                       foreground=self.theme["text_primary"],
                       fieldbackground=self.theme["bg_widget"],
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=self.theme["bg_secondary"],
                       foreground=self.theme["accent_blue"],
                       relief="flat")
        style.map("Treeview", 
                 background=[('selected', self.theme["bg_selected"])])
        
        # Configure columns
        self.tree.column("#0", width=250, anchor="w")
        self.tree.column("Size", width=80, anchor="e")
        self.tree.column("Type", width=80, anchor="center")
        self.tree.column("Modified", width=120, anchor="center")
        
        # Headings
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("Size", text="Size", anchor="center")
        self.tree.heading("Type", text="Type", anchor="center")
        self.tree.heading("Modified", text="Modified", anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", 
                                 command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double click
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Buttons
        btn_frame = tk.Frame(self, bg=self.theme["bg_secondary"])
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        buttons = [
            ("New File", self.create_file, self.theme["accent_green"]),
            ("New Folder", self.create_folder, self.theme["accent_blue"]),
            ("Delete", self.delete_selected, self.theme["accent_red"]),
            ("Open", self.open_selected, self.theme["accent_purple"]),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                          bg=color, fg="white",
                          relief="flat", padx=10)
            btn.pack(side="left", padx=2)
    
    def refresh(self):
        """Refresh file list"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update directory label
        self.dir_label.config(text=self.fs.current_dir)
        
        # Update navigation buttons
        dir_info = self.fs.directory_history
        idx = self.fs.history_index
        self.back_btn.config(state="normal" if idx > 0 else "disabled")
        self.forward_btn.config(state="normal" if idx < len(dir_info) - 1 else "disabled")
        
        # Get files
        files = self.fs.get_current_files()
        
        # Add to tree
        for file in files:
            size = self.fs.format_size(file['size']) if file['type'] == 'file' else "<DIR>"
            item_id = self.tree.insert("", "end",
                                      text=file['name'],
                                      values=(size, 
                                              file['type'].upper(),
                                              file.get('modified', '')))
            
            # Tag special items
            if file.get('is_special', False):
                self.tree.item(item_id, tags=("special",))
            elif file.get('is_new', False):
                self.tree.item(item_id, tags=("new",))
            elif file['type'] == 'folder':
                self.tree.item(item_id, tags=("folder",))
            else:
                self.tree.item(item_id, tags=("file",))
        
        # Configure tags
        self.tree.tag_configure("special", foreground=self.theme["accent_yellow"])
        self.tree.tag_configure("new", foreground=self.theme["accent_green"])
        self.tree.tag_configure("folder", foreground=self.theme["accent_blue"])
        self.tree.tag_configure("file", foreground=self.theme["text_primary"])
    
    def go_back(self):
        """Go back in history"""
        self.app.execute_command("back")
    
    def go_forward(self):
        """Go forward in history"""
        self.app.execute_command("forward")
    
    def on_double_click(self, event):
        """Handle double click"""
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        filename = item['text']
        
        if filename == "..":
            self.app.execute_command("cd ..")
        elif item['values'][1] == 'FOLDER':
            self.app.execute_command(f"cd {filename}")
        else:
            self.open_file(filename)
    
    def create_file(self):
        """Create new file"""
        import tkinter.simpledialog as sd
        filename = sd.askstring("Create File", "Enter filename:")
        if filename:
            self.app.execute_command(f"touch {filename}")
    
    def create_folder(self):
        """Create new folder"""
        import tkinter.simpledialog as sd
        foldername = sd.askstring("Create Folder", "Enter folder name:")
        if foldername:
            self.app.execute_command(f"mkdir {foldername}")
    
    def delete_selected(self):
        """Delete selected file"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a file/folder first")
            return
        
        item = self.tree.item(selected[0])
        filename = item['text']
        
        if filename == "..":
            messagebox.showinfo("Info", "Cannot delete parent directory")
            return
        
        if messagebox.askyesno("Confirm", f"Delete '{filename}'?"):
            self.app.execute_command(f"rm {filename}")
    
    def open_selected(self):
        """Open selected file"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a file/folder first")
            return
        
        item = self.tree.item(selected[0])
        filename = item['text']
        
        if filename == "..":
            self.app.execute_command("cd ..")
        elif item['values'][1] == 'FOLDER':
            self.app.execute_command(f"cd {filename}")
        else:
            self.open_file(filename)
    
    def open_file(self, filename):
        """Open a file"""
        filepath = os.path.join(self.fs.current_dir, filename)
        try:
            webbrowser.open(filepath)
        except:
            messagebox.showerror("Error", f"Cannot open: {filename}")