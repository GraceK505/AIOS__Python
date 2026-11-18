#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS - Modular Version
Main entry point
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    print("=" * 60)
    print("AIOS - Artificial Intelligence Operating System")
    print("Modular Version 4.0")
    print("=" * 60)
    
    try:
        # Check dependencies
        try:
            import psutil
            import tkinter as tk
        except ImportError as e:
            print(f"Missing dependency: {e}")
            print("\nPlease install required packages:")
            print("pip install psutil")
            return
        
        # Import after checking dependencies
        from gui import AIOSApp
        
        print("Starting AIOS...")
        print(f"Workspace: {os.path.join(os.getcwd(), 'aios_workspace')}")
        
        # Create main window
        root = tk.Tk()
        app = AIOSApp(root)
        
        # Start application
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nAIOS interrupted by user")
    except Exception as e:
        print(f"\nError starting AIOS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()