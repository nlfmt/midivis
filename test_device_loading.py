#!/usr/bin/env python3
"""
Test script to verify device loading logic
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.ui.main_window import MainWindow

def test_device_loading():
    """Test the device loading sequence"""
    print("Starting device loading test...")
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Set up a timer to check the state periodically
    check_count = 0
    def check_state():
        nonlocal check_count
        check_count += 1
        
        print(f"Check {check_count}:")
        print(f"  Devices loaded: {window.devices_loaded}")
        print(f"  Loading settings: {window.loading_device_settings}")
        print(f"  Input devices: {len(window.input_device_map)}")
        print(f"  Output devices: {len(window.output_device_map)}")
        print(f"  Current input: {window.input_device_combo.currentText()}")
        print(f"  Current output: {window.output_device_combo.currentText()}")
        print(f"  Audio streaming: {window.audio_manager.is_streaming()}")
        print()
        
        # Stop after 10 checks (5 seconds)
        if check_count >= 10:
            print("Test completed - shutting down")
            app.quit()
    
    # Check state every 500ms
    timer = QTimer()
    timer.timeout.connect(check_state)
    timer.start(500)
    
    # Run the application
    app.exec()

if __name__ == "__main__":
    test_device_loading()
