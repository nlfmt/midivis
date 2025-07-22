#!/usr/bin/env python3
"""
Quick test script to measure startup performance
"""

import time
import sys
import os

# Add paths for module resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_startup_time():
    """Test how long it takes to show the window"""
    print("Testing startup time...")
    
    start_time = time.time()
    
    # Import Qt
    from PySide6.QtWidgets import QApplication
    qt_import_time = time.time()
    print(f"Qt import: {qt_import_time - start_time:.3f}s")
    
    # Create app
    app = QApplication(sys.argv)
    app_create_time = time.time()
    print(f"App creation: {app_create_time - qt_import_time:.3f}s")
    
    # Import main window
    from ui.main_window import MainWindow
    window_import_time = time.time()
    print(f"MainWindow import: {window_import_time - app_create_time:.3f}s")
    
    # Create window
    window = MainWindow()
    window_create_time = time.time()
    print(f"MainWindow creation: {window_create_time - window_import_time:.3f}s")
    
    # Show window
    window.show()
    window_show_time = time.time()
    print(f"Window show: {window_show_time - window_create_time:.3f}s")
    
    total_time = window_show_time - start_time
    print(f"\nTotal time to show window: {total_time:.3f}s")
    
    # Close immediately for testing
    window.close()
    
    return total_time

if __name__ == "__main__":
    test_startup_time()
