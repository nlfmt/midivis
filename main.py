#!/usr/bin/env python3
"""
Audio Input Streamer - Qt Version

A professional audio streaming application that allows you to stream audio 
from any Windows audio device to your output, with mute functionality.
Perfect for streaming music over Discord while maintaining control.

Author: Audio Streamer Team
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import MainWindow
from theme import apply_theme


def setup_application():
    """Setup and configure the QApplication"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Audio Input Streamer")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AudioStreamer")
    app.setOrganizationDomain("audiostreamer.local")
    
    # High DPI scaling is automatic in Qt 6
    
    # Apply dark theme
    apply_theme(app)
    
    return app


def main():
    """Main application entry point"""
    try:
        # Setup application
        app = setup_application()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
