#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main GUI application for AIOS with Voice Assistant Integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading
import time
from datetime import datetime
import os
import socket
import psutil

import config
from core.filesystem import FileSystemManager
from core.commands import AICore, EnhancedAICore, VoiceAssistant
from core.kernel import KernelMonitor
from .explorer import FileExplorer
from .console import Console
from .monitor import SystemMonitor
from .widget_manager import WidgetManager
from utils.themes import ThemeManager


class AppManager:
    """Windows-style Application Manager with solid style"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.is_visible = False
        self.animation_speed = 10
        self.create_app_manager_window()
    
    def create_app_manager_window(self):
        """Create the app manager window with solid style"""
        theme = self.app.theme_manager.get_theme()
        
        # Create overlay with solid color
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.title("App Manager Overlay")
        self.overlay.geometry(f"{self.parent.winfo_screenwidth()}x{self.parent.winfo_screenheight()}")
        self.overlay.configure(bg=theme["bg_main"])
        self.overlay.attributes('-alpha', 0.0)
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        
        # Center the overlay
        self.overlay.geometry(f"+0+0")
        
        # Create main app manager frame (center of screen)
        self.main_frame = tk.Frame(self.overlay, bg=theme["bg_main"], 
                                   relief='raised', borderwidth=3)
        
        # Calculate position (center of screen)
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        app_width = screen_width // 1.5
        app_height = screen_height // 1.5
        x_pos = (screen_width - app_width) // 2
        y_pos = (screen_height - app_height) // 2
        
        self.main_frame.place(x=x_pos, y=y_pos, width=app_width, height=0)
        
        # Add search bar at top with solid style
        search_frame = tk.Frame(self.main_frame, bg=theme["bg_main"], height=40)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        search_entry = tk.Entry(search_frame, 
                              bg=theme["bg_text"],
                              fg=theme["text_main"],
                              font=("Arial", 10),
                              relief="flat")
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        search_entry.insert(0, "Search applications...")
        
        search_btn = tk.Button(search_frame, text="🔍", 
                             bg=theme["accent_blue"],
                             fg="white",
                             relief="flat",
                             cursor="hand2")
        search_btn.pack(side="right", padx=(5, 0))
        
        # Separator with solid color
        ttk.Separator(self.main_frame, orient='horizontal', style="TSeparator").pack(fill="x", padx=10, pady=5)
        
        # Create application grid (3 columns for better layout)
        apps_frame = tk.Frame(self.main_frame, bg=theme["bg_main"])
        apps_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Define applications with icons and commands
        self.apps = [
            {"name": "Explorer", "icon": "📁", "command": self.app.launch_explorer, "shortcut": "Ctrl+E"},
            {"name": "Monitor", "icon": "📊", "command": self.app.launch_monitor, "shortcut": "Ctrl+M"},
            {"name": "AI Console", "icon": "🤖", "command": self.app.launch_ai_console, "shortcut": "Ctrl+I"},
            {"name": "Voice Assistant", "icon": "🎤", "command": self.app.toggle_voice_assistant, "shortcut": "Ctrl+V"},
            {"name": "Terminal", "icon": "💻", "command": lambda: self.app.open_widget_from_app("terminal"), "shortcut": "F1"},
            {"name": "Calculator", "icon": "🧮", "command": lambda: self.app.open_widget_from_app("calculator"), "shortcut": "F4"},
            {"name": "Network", "icon": "🌐", "command": lambda: self.app.open_widget_from_app("network"), "shortcut": "F5"},
            {"name": "Processes", "icon": "⚙️", "command": lambda: self.app.open_widget_from_app("process"), "shortcut": "F6"},
            {"name": "Notes", "icon": "📝", "command": lambda: self.app.open_widget_from_app("notes"), "shortcut": "F7"},
            {"name": "Screensaver", "icon": "🎬", "command": lambda: self.app.open_widget_from_app("screensaver"), "shortcut": "F3"},
            {"name": "System Info", "icon": "ℹ️", "command": lambda: self.app.open_widget_from_app("info"), "shortcut": "F2"},
            {"name": "Theme", "icon": "🎨", "command": self.app.switch_theme, "shortcut": "Ctrl+T"},
            {"name": "Settings", "icon": "⚙️", "command": self.show_settings, "shortcut": "Ctrl+S"},
        ]
        
        # Create app buttons in a grid
        for i, app in enumerate(self.apps):
            row = i // 3
            col = i % 3
            
            app_frame = tk.Frame(apps_frame, bg=theme["bg_main"])
            app_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Make each column expand equally
            apps_frame.columnconfigure(col, weight=1)
            
            # App icon button with solid background
            app_btn = tk.Button(app_frame, 
                              text=f"{app['icon']}\n{app['name']}",
                              font=("Arial", 9),
                              bg=theme["bg_secondary"],
                              fg=theme["text_main"],
                              relief="flat",
                              cursor="hand2",
                              activebackground=theme["accent_blue"],
                              command=lambda cmd=app['command']: [cmd(), self.animate_close()])
            app_btn.pack(pady=(0, 5))
            
            # Shortcut label with solid background
            shortcut_label = tk.Label(app_frame,
                                    text=app['shortcut'],
                                    font=("Arial", 7),
                                    bg=theme["bg_main"],
                                    fg=theme["text_main"])
            shortcut_label.pack()
            
            # Bind hover effects
            app_btn.bind("<Enter>", lambda e, btn=app_btn: btn.config(bg=theme["accent_blue"]))
            app_btn.bind("<Leave>", lambda e, btn=app_btn: btn.config(bg=theme["bg_secondary"]))
        
        # Bottom bar with user info
        bottom_frame = tk.Frame(self.main_frame, bg=theme["bg_main"], height=40)
        bottom_frame.pack(fill="x", side="bottom")
        
        user_label = tk.Label(bottom_frame, 
                            text=f"🤖 AIOS User",
                            bg=theme["bg_main"],
                            fg=theme["text_main"],
                            font=("Arial", 9))
        user_label.pack(side="left", padx=10)
        
        # Close button with solid background
        close_btn = tk.Button(bottom_frame, text="✕",
                            bg=theme["bg_main"],
                            fg=theme["text_main"],
                            relief="flat",
                            cursor="hand2",
                            activebackground=theme["accent_blue"],
                            command=self.animate_close)
        close_btn.pack(side="right", padx=10)
        
        # Bind events
        self.overlay.bind("<Button-1>", self.handle_click_outside)
        self.overlay.bind("<Escape>", lambda e: self.animate_close())
        self.overlay.bind("<Control-Tab>", lambda e: self.animate_close())
        
        # Hide initially
        self.overlay.withdraw()
    
    def show_settings(self):
        """Show settings window with consistent solid style"""
        theme = self.app.theme_manager.get_theme()
        
        settings_window = tk.Toplevel(self.overlay)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg=theme["bg_main"])
        settings_window.attributes('-topmost', True)
        
        # Position near Settings button
        settings_window.geometry(f"+{self.overlay.winfo_x() + 450}+{self.overlay.winfo_y() + 300}")
        
        # Title with solid background
        tk.Label(settings_window, text="AIOS Settings",
                bg=theme["bg_main"],
                fg=theme["text_header"],
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Theme selector with solid background
        theme_frame = tk.Frame(settings_window, bg=theme["bg_main"])
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(theme_frame, text="Theme:",
                bg=theme["bg_main"],
                fg=theme["text_main"]).pack(side="left", padx=5)
        
        theme_var = tk.StringVar(value=config.GUI_CONFIG["theme"])
        theme_menu = ttk.Combobox(theme_frame, textvariable=theme_var,
                                 values=list(config.THEMES.keys()),
                                 state="readonly")
        theme_menu.pack(side="left", fill="x", expand=True, padx=5)
        
        def apply_theme():
            config.GUI_CONFIG["theme"] = theme_var.get()
            self.app.theme_manager.apply_theme(self.app.root)
            settings_window.destroy()
        
        ttk.Button(theme_frame, text="Apply", 
                  command=apply_theme).pack(side="left", padx=5)
        
        # Animation speed with solid background
        speed_frame = tk.Frame(settings_window, bg=theme["bg_main"])
        speed_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(speed_frame, text="Animation Speed:",
                bg=theme["bg_main"],
                fg=theme["text_main"]).pack(side="left", padx=5)
        
        speed_var = tk.IntVar(value=self.animation_speed)
        speed_scale = tk.Scale(speed_frame, from_=1, to=20,
                              variable=speed_var,
                              orient="horizontal",
                              bg=theme["bg_main"],
                              fg=theme["text_main"],
                              highlightbackground=theme["bg_main"],
                              troughcolor=theme["bg_secondary"],
                              length=150)
        speed_scale.pack(side="left", padx=5)
        
        def update_speed():
            self.animation_speed = speed_var.get()
        
        speed_scale.config(command=lambda v: update_speed())
        
        # Voice settings
        voice_frame = tk.Frame(settings_window, bg=theme["bg_main"])
        voice_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(voice_frame, text="Voice Assistant:",
                bg=theme["bg_main"],
                fg=theme["text_main"]).pack(side="left", padx=5)
        
        voice_status = tk.Label(voice_frame,
                               text="Available" if hasattr(self.app, 'voice_assistant') and self.app.voice_assistant.voice_enabled else "Not Available",
                               bg=theme["bg_main"],
                               fg=theme["accent_green"] if hasattr(self.app, 'voice_assistant') and self.app.voice_assistant.voice_enabled else theme["text_main"])
        voice_status.pack(side="left", padx=5)
        
        # Close button with solid style
        close_frame = tk.Frame(settings_window, bg=theme["bg_main"])
        close_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(close_frame, text="Close",
                 bg=theme["bg_secondary"],
                 fg=theme["text_main"],
                 relief="flat",
                 command=settings_window.destroy).pack(side="right")
    
    def handle_click_outside(self, event):
        """Handle clicks outside the app manager"""
        if not self.main_frame.winfo_containing(event.x_root, event.y_root):
            self.animate_close()
    
    def animate_open(self):
        """Animate opening the app manager"""
        if self.is_visible:
            return
        
        self.is_visible = True
        self.overlay.deiconify()
        
        # Start with overlay fully transparent and main frame height 0
        self.overlay.attributes('-alpha', 0.0)
        self.main_frame.place(height=0)
        
        # Animate fade in
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.05
                self.overlay.attributes('-alpha', alpha)
                self.overlay.after(self.animation_speed, lambda: fade_in(alpha))
            else:
                # Animate slide up
                current_height = self.main_frame.winfo_height()
                target_height = 600
                
                def slide_up(height=current_height):
                    if height < target_height:
                        height += 20
                        self.main_frame.place(height=height)
                        self.overlay.after(self.animation_speed // 2, lambda: slide_up(height))
                
                slide_up()
        
        fade_in()
    
    def animate_close(self):
        """Animate closing the app manager"""
        if not self.is_visible:
            return
        
        # Animate slide down
        current_height = self.main_frame.winfo_height()
        
        def slide_down(height=current_height):
            if height > 0:
                height -= 25
                self.main_frame.place(height=height)
                self.overlay.after(self.animation_speed // 2, lambda: slide_down(height))
            else:
                # Animate fade out
                def fade_out(alpha=1.0):
                    if alpha > 0.0:
                        alpha -= 0.05
                        self.overlay.attributes('-alpha', alpha)
                        self.overlay.after(self.animation_speed, lambda: fade_out(alpha))
                    else:
                        self.overlay.withdraw()
                        self.is_visible = False
                
                fade_out()
        
        slide_down()
    
    def toggle(self):
        """Toggle app manager visibility"""
        if self.is_visible:
            self.animate_close()
        else:
            self.animate_open()


class AIOSApp:
    """Main application window - Now a desktop with launcher bar only"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # Initialize components
        self.theme_manager = ThemeManager()
        self.fs = FileSystemManager()
        
        # IMPORTANT: Pass self as callback to AICore
        self.ai = EnhancedAICore(self.fs, app_callback=self.execute_command)
        
        self.update_queue = queue.Queue()
        self.kernel_monitor = KernelMonitor(self.update_queue)
        self.widget_manager = WidgetManager(self)
        
        # Initialize voice assistant
        self.voice_assistant = self.ai.voice
        self.voice_active = False
        self.voice_button = None
        
        # Debug voice assistant initialization
        print(f"\n🔊 Voice Assistant Status:")
        print(f"   Type: {type(self.voice_assistant)}")
        print(f"   Has start_voice_mode: {hasattr(self.voice_assistant, 'start_voice_mode')}")
        print(f"   Voice enabled: {self.voice_assistant.voice_enabled}")
        
        self.create_widgets()
        self.setup_bindings()
        
        # Apply theme and start services
        self.theme_manager.apply_theme(self.root)
        self.kernel_monitor.start()
        self.root.after(100, self.poll_queue)
        
        # Start voice command processor thread
        self.start_voice_processor()
    
    
    def setup_window(self):
        """Setup main window as desktop"""
        self.root.title(config.APP_CONFIG["name"])
        self.root.geometry("800x600")
        self.root.minsize(400, 300)
        
        theme = config.THEMES[config.GUI_CONFIG["theme"]]
        self.root.configure(bg=theme["bg_main"])
        
        # Center window initially
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
    
    def create_widgets(self):
        """Create desktop with only launcher bar"""
        theme = self.theme_manager.get_theme()
        
        # --- Desktop Background ---
        desktop_frame = tk.Frame(self.root, bg=theme["bg_main"])
        desktop_frame.pack(fill="both", expand=True)
        
        # Optional: Add AIOS logo or wallpaper
        logo_label = tk.Label(desktop_frame, 
                            text="🤖\nAIOS",
                            font=("Arial", 48),
                            bg=theme["bg_main"],
                            fg=theme["accent_blue"])
        logo_label.place(relx=0.5, rely=0.4, anchor="center")
        
        instruction_label = tk.Label(desktop_frame,
                                   text="Press Ctrl+Tab to open App Manager\nClick the 🤖 button in launcher",
                                   font=("Arial", 12),
                                   bg=theme["bg_main"],
                                   fg=theme["text_main"])
        instruction_label.place(relx=0.5, rely=0.6, anchor="center")
        
        # --- Launcher Bar at the Bottom ---
        launcher_frame = tk.Frame(self.root, bg=theme["bg_main"], height=60)
        launcher_frame.pack(fill="x", side="bottom")
        self.create_launcher_buttons(launcher_frame, theme)
    
    def create_launcher_buttons(self, parent, theme):
        """Create minimal launcher buttons with solid style"""
        # AIOS Start Button (like Windows Start)
        start_btn = tk.Button(parent, text="🤖 AIOS",
                             bg=theme["accent_blue"],
                             fg="white",
                             font=("Arial", 10, "bold"),
                             relief="flat",
                             cursor="hand2",
                             activebackground=theme["accent_blue"],
                             command=self.toggle_app_manager,
                             width=12,
                             height=2)
        start_btn.pack(side="left", padx=(10, 5), pady=5)
        
        # AI Console button with solid style
        console_btn = tk.Button(parent, text="💬 AI Console",
                               bg=theme["bg_secondary"],
                               fg=theme["text_main"],
                               font=("Arial", 9),
                               relief="flat",
                               cursor="hand2",
                               activebackground=theme["accent_blue"],
                               command=self.launch_ai_console,
                               width=12,
                               height=2)
        console_btn.pack(side="left", padx=5, pady=5)
        
        # Voice Assistant button with solid style
        voice_icon = "🎤" if not self.voice_active else "🔴"
        voice_color = theme["accent_green"] if self.voice_active else theme["bg_secondary"]
        self.voice_button = tk.Button(parent, text=f"{voice_icon} Voice",
                                     bg=voice_color,
                                     fg=theme["text_main"],
                                     font=("Arial", 9),
                                     relief="flat",
                                     cursor="hand2",
                                     activebackground=theme["accent_blue"],
                                     command=self.toggle_voice_assistant,
                                     width=12,
                                     height=2)
        self.voice_button.pack(side="left", padx=5, pady=5)
        
        # Debug button
        debug_btn = tk.Button(parent, text="🔧 Test",
                             bg=theme["bg_secondary"],
                             fg=theme["text_main"],
                             font=("Arial", 9),
                             relief="flat",
                             cursor="hand2",
                             activebackground=theme["accent_blue"],
                             command=lambda: self.debug_voice_command("open terminal"),
                             width=8,
                             height=2)
        debug_btn.pack(side="left", padx=5, pady=5)
        
        # Spacer with solid background
        tk.Label(parent, text="", 
                 bg=theme["bg_main"]).pack(side="left", expand=True)
        
        # System tray area (right side) with solid background
        tray_frame = tk.Frame(parent, bg=theme["bg_main"])
        tray_frame.pack(side="right", padx=5, pady=5)
        
        # Theme switcher button with solid style
        theme_btn = tk.Button(tray_frame, text="🎨",
                             bg=theme["bg_secondary"],
                             fg=theme["text_main"],
                             relief="flat",
                             cursor="hand2",
                             activebackground=theme["accent_blue"],
                             command=self.switch_theme,
                             width=3,
                             height=2)
        theme_btn.pack(side="left", padx=2)
        
        # Time display with solid background
        self.time_label = tk.Label(tray_frame,
                                 text=datetime.now().strftime("%H:%M"),
                                 bg=theme["bg_main"],
                                 fg=theme["text_main"],
                                 font=("Arial", 10))
        self.time_label.pack(side="left", padx=5)
        self.update_time()
    
    def update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%H:%M")
        self.time_label.config(text=current_time)
        self.root.after(60000, self.update_time)
    
    def toggle_app_manager(self):
        """Toggle the app manager window"""
        if not hasattr(self, 'app_manager'):
            self.app_manager = AppManager(self.root, self)
        self.app_manager.toggle()
    
    def switch_theme(self):
        """Switch to next theme"""
        self.theme_manager.cycle_theme(self.root)
        theme = self.theme_manager.get_theme()
        self.root.winfo_children()[1].configure(bg=theme["bg_main"])
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        # App Manager shortcut (Ctrl+Tab)
        self.root.bind("<Control-Tab>", lambda e: self.toggle_app_manager())
        
        # AI Console shortcut (Ctrl+I)
        self.root.bind("<Control-i>", lambda e: self.launch_ai_console())
        self.root.bind("<Control-I>", lambda e: self.launch_ai_console())
        
        # Voice Assistant shortcut (Ctrl+V)
        self.root.bind("<Control-v>", lambda e: self.toggle_voice_assistant())
        self.root.bind("<Control-V>", lambda e: self.toggle_voice_assistant())
        
        # Quick voice command (Ctrl+Shift+V)
        self.root.bind("<Control-Shift-v>", lambda e: self.quick_voice_command())
        self.root.bind("<Control-Shift-V>", lambda e: self.quick_voice_command())
        
        # Widget shortcuts
        self.root.bind("<F1>", lambda e: self.open_widget_from_app("terminal"))
        self.root.bind("<F2>", lambda e: self.open_widget_from_app("info"))
        self.root.bind("<F3>", lambda e: self.open_widget_from_app("screensaver"))
        self.root.bind("<F4>", lambda e: self.open_widget_from_app("calculator"))
        self.root.bind("<F5>", lambda e: self.open_widget_from_app("network"))
        self.root.bind("<F6>", lambda e: self.open_widget_from_app("process"))
        self.root.bind("<F7>", lambda e: self.open_widget_from_app("notes"))
        
        # Quick launch shortcuts
        self.root.bind("<Control-e>", lambda e: self.launch_explorer())
        self.root.bind("<Control-m>", lambda e: self.launch_monitor())
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_voice_processor(self):
        """Start background thread to process voice commands - WORKING VERSION"""
        def process_voice_commands():
            print("🎤 Voice processor thread started")
            while True:
                try:
                    # Check for voice commands
                    if self.voice_assistant and hasattr(self.voice_assistant, 'command_queue'):
                        if not self.voice_assistant.command_queue.empty():
                            source, command, response = self.voice_assistant.command_queue.get()
                            print(f"\n🎤 [Voice] Command received: {command}")
                            print(f"💬 [Voice] Response: {response[:200]}...")
                            
                            # Update console if open
                            if hasattr(self, 'console'):
                                self.console.write(f"\n[Voice] Command: {command}\n", "info")
                                self.console.write(f"[Voice] Response: {response[:200]}...\n\n")
                            
                            # Process widget commands from response
                            if isinstance(response, str):
                                if "[WIDGET:" in response:
                                    # Extract widget name from [WIDGET:TERMINAL]
                                    widget_name = response[8:-1].lower()
                                    print(f"🎯 Widget command detected: {widget_name}")
                                    self.open_widget_from_app(widget_name)
                                elif "widget" in response.lower() or "open" in response.lower():
                                    # Try to extract widget name
                                    widget_names = ['terminal', 'calculator', 'notes', 'info', 
                                                  'screensaver', 'network', 'process', 'explorer', 
                                                  'monitor', 'console']
                                    for widget in widget_names:
                                        if widget in response.lower():
                                            print(f"🎯 Opening widget: {widget}")
                                            self.open_widget_from_app(widget)
                                            break
                    
                    # Small delay to prevent CPU overuse
                    time.sleep(0.1)
                except Exception as e:
                    print(f"❌ Voice processor error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=process_voice_commands, daemon=True)
        thread.start()
        print("✅ Voice processor thread started successfully")
    
    def debug_voice_command(self, command_text):
        """Manually test voice command processing"""
        print(f"\n🧪 Testing voice command: '{command_text}'")
        
        if not hasattr(self, 'voice_assistant'):
            print("❌ Voice assistant not available")
            return
        
        # Process command directly
        matrix, response = self.voice_assistant.process_voice_command(command_text)
        print(f"📊 Matrix confidence: {matrix.get('confidence_score', 0):.1%}")
        print(f"💬 Response: {response}")
        
        # Update console if open
        if hasattr(self, 'console'):
            self.console.write(f"\n[Debug] Command: {command_text}\n", "info")
            self.console.write(f"[Debug] Response: {response}\n\n")
        
        return response
    
    def toggle_voice_assistant(self):
        """Toggle voice assistant on/off - WORKING VERSION"""
        if not hasattr(self, 'voice_assistant') or not self.voice_assistant:
            messagebox.showinfo("Voice Assistant", "Voice assistant not available.\nInstall: pip install speechrecognition pyttsx3")
            return
        
        if not self.voice_assistant.voice_enabled:
            messagebox.showinfo("Voice Assistant", "Voice modules not available.\nInstall: pip install speechrecognition pyttsx3")
            return
        
        theme = self.theme_manager.get_theme()
        
        if self.voice_active:
            # Stop voice assistant
            if hasattr(self.voice_assistant, 'stop_voice_mode'):
                result = self.voice_assistant.stop_voice_mode()
            else:
                self.voice_assistant.voice_active = False
            
            self.voice_active = False
            self.voice_button.config(text="🎤 Voice", bg=theme["bg_secondary"])
            
            if hasattr(self, 'console'):
                self.console.write("Voice assistant stopped\n\n", "info")
        else:
            # Start voice assistant
            try:
                if hasattr(self.voice_assistant, 'start_voice_mode'):
                    result = self.voice_assistant.start_voice_mode()
                else:
                    # Fallback
                    self.voice_assistant.voice_active = True
                    self.voice_assistant.speak("Voice assistant activated")
                    
                    # Start voice thread if not already running
                    if not self.voice_assistant.voice_thread or not self.voice_assistant.voice_thread.is_alive():
                        self.voice_assistant.voice_thread = threading.Thread(
                            target=self.voice_assistant._voice_loop, 
                            daemon=True
                        )
                        self.voice_assistant.voice_thread.start()
                    
                    result = "Voice assistant started"
                
                self.voice_active = True
                self.voice_button.config(text="🔴 Voice", bg=theme["accent_green"])
                
                if hasattr(self, 'console'):
                    self.console.write(f"{result}\nSay 'Hey AIOS' followed by your command\n\n", "info")
                
                # Show notification
                messagebox.showinfo("Voice Assistant", result)
                
            except Exception as e:
                error_msg = f"Error starting voice assistant: {str(e)}"
                print(error_msg)
                messagebox.showerror("Voice Assistant Error", error_msg)
    
    def quick_voice_command(self):
        """Execute a quick voice command (single listen)"""
        if not hasattr(self, 'voice_assistant') or not self.voice_assistant:
            messagebox.showinfo("Voice Assistant", "Voice assistant not available")
            return
        
        if not self.voice_assistant.voice_enabled:
            messagebox.showinfo("Voice Assistant", "Voice modules not available")
            return
        
        # Listen for a single command
        if hasattr(self, 'console'):
            self.console.write("🎤 Listening for voice command...\n", "info")
        
        command = self.voice_assistant.listen(timeout=5)
        
        if command and command not in ["Listening timeout", "Could not understand audio"]:
            if hasattr(self, 'console'):
                self.console.write(f"🗣️ Heard: {command}\n", "info")
            
            # Process the command through AI
            response = self.voice_assistant.voice_ai_chat(command)
            
            if hasattr(self, 'console'):
                self.console.write(f"🤖 Response: {response[:200]}...\n\n")
            
            # Process any widget commands
            if isinstance(response, str):
                if "[WIDGET:" in response:
                    widget_name = response[8:-1].lower()
                    self.open_widget_from_app(widget_name)
        else:
            if hasattr(self, 'console'):
                self.console.write(f"❌ Voice input failed: {command}\n\n", "error")
    
    def launch_ai_console(self):
        """Launch AI Console as separate application window with consistent style"""
        if hasattr(self, 'console_window') and self.console_window.winfo_exists():
            self.console_window.lift()
            self.console_window.focus_force()
            return
        
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("AIOS - AI Console")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set to full screen (with space for taskbar)
        self.console_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        theme = config.THEMES[config.GUI_CONFIG["theme"]]
        self.console_window.configure(bg=theme["bg_main"])
        self.console_window.attributes('-topmost', True)
        
        # Create the Console instance
        console_frame = tk.Frame(self.console_window, bg=theme["bg_main"])
        console_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.console = Console(console_frame, self)
        self.console.pack(fill="both", expand=True)
        
        # Write welcome message
        self.write_welcome()
        
        self.console_window.protocol("WM_DELETE_WINDOW", self.on_console_close)
        
        # Bind Ctrl+W to close console window
        self.console_window.bind("<Control-w>", lambda e: self.on_console_close())
        self.console_window.bind("<Control-W>", lambda e: self.on_console_close())
    
    def write_welcome(self):
        """Write welcome message to console"""
        if hasattr(self, 'console'):
            self.console.clear()
            
            # Simple ASCII logo
            self.console.write("┌───────────────────────────────────────┐\n", "accent_blue")
            self.console.write("│      🤖 AIOS v4.0                     │\n", "accent_blue")
            self.console.write("│  Artificial Intelligence OS           │\n", "accent_blue")
            self.console.write("└───────────────────────────────────────┘\n\n", "accent_blue")
            self.console.write("=" * 60 + "\n")
            self.console.write(f"{config.APP_CONFIG['name']} v{config.APP_CONFIG['version']}\n")
            self.console.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.console.write("=" * 60 + "\n\n")
            self.console.write("Type 'help' for available commands\n")
            self.console.write("Press Ctrl+Tab to open App Manager\n")
            self.console.write("Press Ctrl+I to open this console\n")
            self.console.write("Press Ctrl+V to toggle Voice Assistant\n")
            self.console.write("Press Ctrl+Shift+V for quick voice command\n")
            self.console.write("Press Ctrl+W to close this console\n")
            self.console.write("Press F1-F7 for quick widget access\n")
            self.console.write("Type 'monitor' for system dashboard\n\n")
            
            # Voice assistant status
            if hasattr(self, 'voice_assistant') and self.voice_assistant.voice_enabled:
                status = "ACTIVE" if self.voice_active else "INACTIVE"
                self.console.write(f"Voice Assistant: {status}\n", "info")
            else:
                self.console.write("Voice Assistant: Not available (install speechrecognition, pyttsx3)\n", "warning")
    
    def on_console_close(self):
        """Handle console window close"""
        if hasattr(self, 'console_window'):
            self.console_window.destroy()
            delattr(self, 'console_window')
            if hasattr(self, 'console'):
                delattr(self, 'console')
    
    def execute_command(self, cmd):
        """Execute a command in the console if it's open"""
        # If cmd is a widget name (from voice), open the widget
        widget_names = ['terminal', 'calculator', 'notes', 'info', 
                   'screensaver', 'network', 'process', 'explorer', 
                   'monitor', 'console']
    
        # Check if it's a direct widget name
        if isinstance(cmd, str) and cmd in widget_names:
            self.open_widget_from_app(cmd)
            return f"Opening {cmd} widget"
        
        # Process as regular command
        cmd_lower = cmd.strip().lower()
        
        # Process command through AI core
        response, refresh, special = self.ai.process_command(cmd)
        
        if special:
            if response == "[CLEAR]":
                if hasattr(self, 'console'):
                    self.console.clear()
                    self.write_welcome()
                return "[CLEAR]"
            elif response == "[SHUTDOWN]":
                self.on_closing()
                return "[SHUTDOWN]"
            elif response == "[MONITOR]":
                if hasattr(self, 'console'):
                    self.show_monitor_dashboard()
                return "[MONITOR]"
            elif response.startswith("[WIDGET:"):
                # Extract widget name from [WIDGET:TERMINAL]
                widget_name = response[8:-1].lower()
                if widget_name in widget_names:
                    self.open_widget_from_app(widget_name)
                    return f"Opening {widget_name} widget"
        
        return response
    
    # =================== APPLICATION LAUNCHERS ===================
    
    def launch_explorer(self):
        """Launch File Explorer as separate application window with consistent style"""
        if hasattr(self, 'explorer_window') and self.explorer_window.winfo_exists():
            self.explorer_window.lift()
            self.explorer_window.focus_force()
            return
        
        self.explorer_window = tk.Toplevel(self.root)
        self.explorer_window.title("AIOS - File Explorer")
        self.explorer_window.geometry("900x600")
        
        theme = config.THEMES[config.GUI_CONFIG["theme"]]
        self.explorer_window.configure(bg=theme["bg_main"])
        
        # Position window offset from main window
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 50
        self.explorer_window.geometry(f"+{x}+{y}")
        self.explorer_window.transient(self.root)
        
        # Create the FileExplorer instance
        self.explorer_app = FileExplorer(self.explorer_window, self.fs, self)
        self.explorer_app.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.explorer_window.protocol("WM_DELETE_WINDOW", self.on_explorer_close)
    
    def on_explorer_close(self):
        """Handle explorer window close"""
        if hasattr(self, 'explorer_window'):
            self.explorer_window.destroy()
            delattr(self, 'explorer_window')
    
    def launch_monitor(self):
        """Launch System Monitor as separate application window with consistent style"""
        if hasattr(self, 'monitor_window') and self.monitor_window.winfo_exists():
            self.monitor_window.lift()
            self.monitor_window.focus_force()
            return
        
        self.monitor_window = tk.Toplevel(self.root)
        self.monitor_window.title("AIOS - System Monitor")
        self.monitor_window.geometry("700x500")
        
        theme = config.THEMES[config.GUI_CONFIG["theme"]]
        self.monitor_window.configure(bg=theme["bg_main"])
        
        # Position window
        x = self.root.winfo_x() + 100
        y = self.root.winfo_y() + 100
        self.monitor_window.geometry(f"+{x}+{y}")
        self.monitor_window.attributes('-topmost', True)
        
        # Create the SystemMonitor instance
        self.monitor_app = SystemMonitor(self.monitor_window)
        self.monitor_app.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.monitor_window.protocol("WM_DELETE_WINDOW", self.on_monitor_close)
    
    def on_monitor_close(self):
        """Handle monitor window close"""
        if hasattr(self, 'monitor_window'):
            self.monitor_window.destroy()
            delattr(self, 'monitor_window')
    
    # =================== WIDGET METHODS ===================
    
    def open_widget_from_app(self, widget_name):
        """Open a widget by name"""
        print(f"📱 Opening widget: {widget_name}")
        
        widget_methods = {
            'terminal': self.open_terminal_widget,
            'calculator': self.open_calculator_widget,
            'notes': self.open_notes_widget,
            'info': self.open_info_widget,
            'screensaver': self.open_screensaver_widget,
            'network': self.open_network_widget,
            'process': self.open_process_widget,
            'explorer': self.launch_explorer,
            'monitor': self.launch_monitor,
            'console': self.launch_ai_console
        }
        
        if widget_name in widget_methods:
            widget_methods[widget_name]()
            return f"Opening {widget_name} widget"
        else:
            return f"Unknown widget: {widget_name}"
    
    def open_terminal_widget(self):
        """Open terminal widget with consistent style"""
        if self.widget_manager.is_open("terminal"):
            self.widget_manager.widget_windows["terminal"].lift()
            self.widget_manager.widget_windows["terminal"].focus_force()
            return
        
        def create_terminal_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            tk.Label(frame, text="Quick Terminal",
                    bg=theme["bg_main"],
                    fg=theme["text_header"],
                    font=("Arial", 12, "bold")).pack(pady=10)
            
            text_widget = tk.Text(frame, height=15, width=50,
                                 bg=theme["bg_text"],
                                 fg=theme["text_main"])
            text_widget.pack(padx=10, pady=5)
            
            input_frame = tk.Frame(frame, bg=theme["bg_main"])
            input_frame.pack(fill="x", padx=10, pady=5)
            
            entry_var = tk.StringVar()
            entry = tk.Entry(input_frame, textvariable=entry_var,
                           bg=theme["bg_text"],
                           fg=theme["text_main"])
            entry.pack(side="left", fill="x", expand=True)
            
            def execute_command():
                cmd = entry_var.get().strip()
                if cmd:
                    text_widget.insert("end", f"\n$ {cmd}\n")
                    entry_var.set("")
                    text_widget.insert("end", f"Executing: {cmd}\n")
            
            ttk.Button(input_frame, text="Run", 
                      command=execute_command).pack(side="left", padx=5)
            
            return frame
        
        window = self.widget_manager.open_widget_window("terminal", create_terminal_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> terminal\n")
            self.console.write("Terminal widget opened\n\n", "info")
    
    def open_info_widget(self):
        """Open info widget with consistent style"""
        if self.widget_manager.is_open("info"):
            self.widget_manager.widget_windows["info"].lift()
            self.widget_manager.widget_windows["info"].focus_force()
            return
        
        def create_info_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            info_text = f"""AIOS System Information
                        Version: {config.APP_CONFIG['version']}
                        Theme: {config.GUI_CONFIG['theme']}
                        Widgets Available: 7
                        Voice Assistant: {'Available' if hasattr(self, 'voice_assistant') and self.voice_assistant.voice_enabled else 'Not Available'}

                        Voice Commands:
                        - Press Ctrl+V to toggle Voice Assistant
                        - Press Ctrl+Shift+V for quick voice command
                        - Say "Hey AIOS" followed by command

                        Press F1 for Terminal
                        Press F2 for Info
                        Press F3 for Screensaver
                        Press F4 for Calculator
                        Press F5 for Network
                        Press F6 for Process Viewer
                        Press F7 for Notes

                        Type 'help' for commands
                        Type 'clear' to clear console
                        Type 'exit' to quit"""
            
            text_widget = tk.Text(frame, height=15, width=50,
                                 bg=theme["bg_main"],
                                 fg=theme["text_main"],
                                 relief="flat")
            text_widget.insert("1.0", info_text)
            text_widget.config(state="disabled")
            text_widget.pack(padx=10, pady=10)
            
            return frame
        
        window = self.widget_manager.open_widget_window("info", create_info_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> info\n")
            self.console.write("Info widget opened\n\n", "info")
    
    def open_screensaver_widget(self):
        """Open screensaver widget"""
        if self.widget_manager.is_open("screensaver"):
            self.widget_manager.widget_windows["screensaver"].lift()
            self.widget_manager.widget_windows["screensaver"].focus_force()
            return
        
        def create_screensaver_content(parent):
            frame = tk.Frame(parent, bg="black")
            canvas = tk.Canvas(frame, bg="black", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            text_id = canvas.create_text(200, 150, 
                                       text="AIOS",
                                       fill="green",
                                       font=("Courier", 48))
            
            dx, dy = 2, 1
            
            def animate():
                nonlocal dx, dy
                canvas.move(text_id, dx, dy)
                x1, y1, x2, y2 = canvas.bbox(text_id)
                if x1 <= 0 or x2 >= 400:
                    dx = -dx
                if y1 <= 0 or y2 >= 300:
                    dy = -dy
                canvas.after(20, animate)
            
            animate()
            return frame
        
        window = self.widget_manager.open_widget_window("screensaver", create_screensaver_content)
        window.geometry("800x600")
        window.attributes('-fullscreen', True)
        window.attributes('-topmost', True)
        
        def exit_screensaver(event):
            window.attributes('-fullscreen', False)
            window.geometry("400x300")
            self.widget_manager.close_widget_window("screensaver")
        
        window.bind("<Escape>", exit_screensaver)
        window.bind("<Any-Key>", exit_screensaver)
        window.bind("<Button-1>", exit_screensaver)
        
        if hasattr(self, 'console'):
            self.console.write(f">> screensaver\n")
            self.console.write("Screensaver activated (Press any key to exit)\n\n", "info")
    
    def open_calculator_widget(self):
        """Open calculator widget with consistent style"""
        if self.widget_manager.is_open("calculator"):
            self.widget_manager.widget_windows["calculator"].lift()
            self.widget_manager.widget_windows["calculator"].focus_force()
            return
        
        def create_calculator_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            display_var = tk.StringVar()
            display_var.set("0")
            
            display = tk.Entry(frame, textvariable=display_var,
                              font=("Arial", 18),
                              bg=theme["bg_text"],
                              fg=theme["text_main"],
                              justify="right",
                              relief="sunken")
            display.grid(row=0, column=0, columnspan=4, 
                        padx=10, pady=10, sticky="ew")
            
            buttons = [
                '7', '8', '9', '/',
                '4', '5', '6', '*',
                '1', '2', '3', '-',
                '0', '.', '=', '+'
            ]
            
            row, col = 1, 0
            for btn_text in buttons:
                ttk.Button(frame, text=btn_text, 
                          command=lambda t=btn_text: self.calc_button_click(t, display_var),
                          width=5).grid(row=row, column=col, padx=2, pady=2)
                col += 1
                if col > 3:
                    col = 0
                    row += 1
            
            ttk.Button(frame, text="C",
                      command=lambda: display_var.set("0"),
                      width=5).grid(row=row, column=0, columnspan=2, padx=2, pady=2)
            
            return frame
        
        window = self.widget_manager.open_widget_window("calculator", create_calculator_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> calculator\n")
            self.console.write("Calculator widget opened\n\n", "info")
    
    def calc_button_click(self, button_text, display_var):
        """Handle calculator button clicks"""
        current = display_var.get()
        
        if button_text == '=':
            try:
                result = eval(current)
                display_var.set(str(result))
            except:
                display_var.set("Error")
        elif button_text == 'C':
            display_var.set("0")
        else:
            if current == "0" or current == "Error":
                display_var.set(button_text)
            else:
                display_var.set(current + button_text)
    
    def open_network_widget(self):
        """Open network widget with consistent style"""
        if self.widget_manager.is_open("network"):
            self.widget_manager.widget_windows["network"].lift()
            self.widget_manager.widget_windows["network"].focus_force()
            return
        
        def create_network_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                info_text = f"""Network Information:

Hostname: {hostname}
IP Address: {ip}"""
            except:
                info_text = "Network information unavailable"
            
            text_widget = tk.Text(frame, height=10, width=50,
                                 bg=theme["bg_main"],
                                 fg=theme["text_main"])
            text_widget.insert("1.0", info_text)
            text_widget.config(state="disabled")
            text_widget.pack(padx=10, pady=10)
            
            return frame
        
        window = self.widget_manager.open_widget_window("network", create_network_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> network\n")
            self.console.write("Network widget opened\n\n", "info")
    
    def open_process_widget(self):
        """Open process widget with consistent style"""
        if self.widget_manager.is_open("process"):
            self.widget_manager.widget_windows["process"].lift()
            self.widget_manager.widget_windows["process"].focus_force()
            return
        
        def create_process_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            listbox = tk.Listbox(frame, width=60, height=15,
                                bg=theme["bg_text"],
                                fg=theme["text_main"])
            listbox.pack(padx=10, pady=10, fill="both", expand=True)
            
            def refresh_processes():
                listbox.delete(0, "end")
                for proc in list(psutil.process_iter(['pid', 'name']))[:15]:
                    try:
                        listbox.insert("end", f"PID {proc.info['pid']}: {proc.info['name']}")
                    except:
                        pass
            
            refresh_processes()
            
            ttk.Button(frame, text="Refresh", 
                      command=refresh_processes).pack(pady=5)
            
            return frame
        
        window = self.widget_manager.open_widget_window("process", create_process_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> process\n")
            self.console.write("Process widget opened\n\n", "info")
    
    def open_notes_widget(self):
        """Open notes widget with consistent style"""
        if self.widget_manager.is_open("notes"):
            self.widget_manager.widget_windows["notes"].lift()
            self.widget_manager.widget_windows["notes"].focus_force()
            return
        
        def create_notes_content(parent):
            theme = config.THEMES[config.GUI_CONFIG["theme"]]
            frame = tk.Frame(parent, bg=theme["bg_main"])
            
            text_widget = tk.Text(frame, height=15, width=50,
                                 bg=theme["bg_text"],
                                 fg=theme["text_main"])
            text_widget.pack(padx=10, pady=10, fill="both", expand=True)
            
            # Load existing notes
            notes_file = "quick_notes.txt"
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, "r") as f:
                        text_widget.insert("1.0", f.read())
                except:
                    pass
            
            def save_notes():
                with open(notes_file, "w") as f:
                    f.write(text_widget.get("1.0", "end-1c"))
            
            ttk.Button(frame, text="Save Notes", 
                      command=save_notes).pack(pady=5)
            
            return frame
        
        window = self.widget_manager.open_widget_window("notes", create_notes_content)
        window.attributes('-topmost', True)
        
        if hasattr(self, 'console'):
            self.console.write(f">> notes\n")
            self.console.write("Notes widget opened\n\n", "info")
    
    # =================== SYSTEM METHODS ===================
    
    def show_monitor_dashboard(self):
        """Show monitor dashboard in console"""
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if hasattr(self, 'console'):
            self.console.write("System Monitor Dashboard:\n", "info")
            self.console.write(f"CPU: {cpu}%\n")
            self.console.write(f"Memory: {mem.percent}% ({mem.used//(1024**2)}MB / {mem.total//(1024**3)}GB)\n")
            self.console.write(f"Disk: {disk.percent}% ({disk.used//(1024**3)}GB / {disk.total//(1024**3)}GB)\n\n")
    
    def refresh_file_explorer(self):
        """Refresh file explorer"""
        if hasattr(self, 'explorer_app') and hasattr(self, 'explorer_window'):
            if self.explorer_window.winfo_exists():
                self.explorer_app.refresh()
    
    def poll_queue(self):
        """Poll update queue"""
        try:
            while True:
                msg_type, data = self.update_queue.get_nowait()
                
                if msg_type == "update":
                    # Update monitor if window is open
                    if hasattr(self, 'monitor_window') and self.monitor_window.winfo_exists():
                        if hasattr(self, 'monitor_app'):
                            self.monitor_app.update(data)
                    
                    # Show alerts in console if open
                    alerts = data.get("alerts", [])
                    if alerts and hasattr(self, 'console'):
                        for alert in alerts:
                            self.console.write(f"[ALERT] {alert}\n", "warning")
                
                elif msg_type == "error":
                    if hasattr(self, 'console'):
                        self.console.write(f"{data}\n\n", "error")
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self.poll_queue)
    
    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("Quit", "Do you want to quit AIOS?"):
            self.kernel_monitor.stop()
            
            # Stop voice assistant if active
            if hasattr(self, 'voice_assistant') and self.voice_active:
                self.voice_assistant.stop_voice_mode()
            
            # Close app manager if open
            if hasattr(self, 'app_manager') and hasattr(self.app_manager, 'overlay'):
                self.app_manager.overlay.destroy()
            
            # Close all application windows
            for window_attr in ['console_window', 'explorer_window', 'monitor_window']:
                if hasattr(self, window_attr) and getattr(self, window_attr).winfo_exists():
                    getattr(self, window_attr).destroy()
            
            # Close all widget windows via widget manager
            if hasattr(self, 'widget_manager'):
                self.widget_manager.close_all()
            
            # Cleanup AI core
            if hasattr(self, 'ai'):
                self.ai.cleanup()
            
            self.root.destroy()


# ==================== MAIN ENTRY POINT ====================
def main():
    """Main entry point"""
    root = tk.Tk()
    app = AIOSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()