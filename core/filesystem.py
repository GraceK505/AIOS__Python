#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File system management for AIOS
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import config

class FileSystemManager:
    """Manages file system operations with history tracking"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or config.FILESYSTEM_CONFIG["workspace"]
        self.current_dir = os.getcwd()
        self.file_history = []
        self.created_files = set()
        self.created_dirs = set()
        self.directory_history = [self.current_dir]
        self.history_index = 0
        
        # Setup workspace
        self._setup_workspace()
    
    def _setup_workspace(self):
        """Initialize the workspace directory"""
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir, exist_ok=True)
            self._create_default_structure()
    
    def _create_default_structure(self):
        """Create default directory structure"""
        default_dirs = [
            "documents", "projects", "data", "temp",
            "logs", "scripts", "configs", "backups"
        ]
        
        for folder in default_dirs:
            os.makedirs(os.path.join(self.workspace_dir, folder), exist_ok=True)
        
        # Create welcome file
        welcome_file = os.path.join(self.workspace_dir, "documents", "welcome.txt")
        with open(welcome_file, 'w', encoding='utf-8') as f:
            f.write("Welcome to AIOS\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("This is your AIOS workspace.\n")
    
    def get_current_files(self) -> List[Dict[str, Any]]:
        """Get list of files in current directory"""
        files = []
        
        try:
            # Add parent directory link if not at root
            parent = os.path.dirname(self.current_dir)
            if parent != self.current_dir:
                files.append({
                    "name": "..",
                    "type": "folder",
                    "size": 0,
                    "modified": "",
                    "path": parent,
                    "is_new": False,
                    "is_special": True
                })
            
            for item in os.listdir(self.current_dir):
                item_path = os.path.join(self.current_dir, item)
                
                # Skip hidden files
                if item.startswith('.') and item not in ['.', '..']:
                    continue
                
                try:
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)
                    
                    files.append({
                        "name": item,
                        "type": "folder" if is_dir else "file",
                        "size": stat.st_size if not is_dir else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "path": item_path,
                        "is_new": item_path in self.created_files or 
                                 (is_dir and item_path in self.created_dirs),
                        "is_special": False
                    })
                except:
                    continue
            
            # Sort: special items first, then folders, then files
            files.sort(key=lambda x: (
                0 if x.get('is_special', False) else 1,
                0 if x["type"] == "folder" else 2,
                x["name"].lower()
            ))
            return files
        except Exception as e:
            print(f"Error getting files: {e}")
            return []
    
    def create_file(self, filename: str, content: str = "") -> Tuple[bool, str]:
        """Create a new file"""
        try:
            if '.' not in filename:
                filename += ".txt"
            
            filepath = os.path.join(self.current_dir, filename)
            
            if os.path.exists(filepath):
                return False, f"File already exists: {filename}"
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if not content:
                    f.write(f"# Created by AIOS at {datetime.now()}\n")
                else:
                    f.write(content)
            
            self.created_files.add(filepath)
            return True, f"File created: {filename}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def create_folder(self, foldername: str) -> Tuple[bool, str]:
        """Create a new folder"""
        try:
            folderpath = os.path.join(self.current_dir, foldername)
            
            if os.path.exists(folderpath):
                return False, f"Folder already exists: {foldername}"
            
            os.makedirs(folderpath, exist_ok=True)
            self.created_dirs.add(folderpath)
            
            return True, f"Folder created: {foldername}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def change_directory(self, path: str) -> Tuple[bool, str]:
        """Change current directory with history tracking"""
        try:
            old_dir = self.current_dir
            
            if path == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            elif path == "~":
                self.current_dir = os.path.expanduser("~")
            elif path == ".":
                return True, "Already in directory"
            else:
                if not os.path.isabs(path):
                    path = os.path.join(self.current_dir, path)
                
                path = os.path.normpath(path)
                
                if not (os.path.exists(path) and os.path.isdir(path)):
                    return False, f"Directory not found: {path}"
                
                self.current_dir = os.path.abspath(path)
            
            # Update history
            if self.current_dir != old_dir:
                if self.history_index < len(self.directory_history) - 1:
                    self.directory_history = self.directory_history[:self.history_index + 1]
                
                self.directory_history.append(self.current_dir)
                self.history_index = len(self.directory_history) - 1
                
                if len(self.directory_history) > 50:
                    self.directory_history = self.directory_history[-50:]
                    self.history_index = len(self.directory_history) - 1
            
            return True, f"Changed to: {self.current_dir}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def go_back(self) -> Tuple[bool, str]:
        """Go back in directory history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_dir = self.directory_history[self.history_index]
            return True, f"Back to: {self.current_dir}"
        return False, "No history"
    
    def go_forward(self) -> Tuple[bool, str]:
        """Go forward in directory history"""
        if self.history_index < len(self.directory_history) - 1:
            self.history_index += 1
            self.current_dir = self.directory_history[self.history_index]
            return True, f"Forward to: {self.current_dir}"
        return False, "No history"
    
    def delete_file(self, filename: str) -> Tuple[bool, str]:
        """Delete a file or folder"""
        try:
            filepath = os.path.join(self.current_dir, filename)
            
            if not os.path.exists(filepath):
                return False, f"File not found: {filename}"
            
            if os.path.isdir(filepath):
                if os.listdir(filepath):
                    return False, f"Directory not empty: {filename}"
                os.rmdir(filepath)
                if filepath in self.created_dirs:
                    self.created_dirs.remove(filepath)
                action = "Folder"
            else:
                os.remove(filepath)
                if filepath in self.created_files:
                    self.created_files.remove(filepath)
                action = "File"
            
            return True, f"{action} deleted: {filename}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get detailed file information"""
        try:
            filepath = os.path.join(self.current_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            stat = os.stat(filepath)
            
            info = {
                "name": filename,
                "path": filepath,
                "type": "folder" if os.path.isdir(filepath) else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "permissions": oct(stat.st_mode)[-3:],
                "is_new": filepath in self.created_files or 
                         (os.path.isdir(filepath) and filepath in self.created_dirs)
            }
            
            return info
        except:
            return None
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"