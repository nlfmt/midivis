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
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# Add paths for module resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
ui_dir = os.path.join(current_dir, 'ui')
core_dir = os.path.join(current_dir, 'core')

# Add all necessary paths
for path in [current_dir, parent_dir, ui_dir, core_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import required modules
try:
    from ui.main_window import MainWindow
    from ui.theme import apply_theme
except ImportError:
    try:
        from main_window import MainWindow
        from theme import apply_theme
    except ImportError as e:
        print(f"Failed to import required modules: {e}")
        sys.exit(1)


def get_icon_path():
    """Get the path to the application icon"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        return os.path.join(application_path, 'icon.ico')
    else:
        # Running as script - icon is in assets/icons
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons', 'icon.ico')


def setup_application():
    """Setup and configure the QApplication"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Audio Input Streamer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Audio Streamer Team")
    
    # Set application icon
    icon_path = get_icon_path()
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Apply dark theme
    apply_theme(app)
    
    return app


def setup_signal_handlers(window):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        if window:
            window.close()
        QApplication.quit()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Enable periodic processing of signals in Qt
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Allow Python signal handlers to run
    timer.start(500)  # Check every 500ms
    return timer


def main():
    """Main application entry point"""
    try:
        # Setup application
        app = setup_application()
        
        # Create and show main window
        window = MainWindow()
        
        # Set window icon
        icon_path = get_icon_path()
        if icon_path and os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
        
        window.show()
        
        # Setup signal handlers for Ctrl+C
        signal_timer = setup_signal_handlers(window)
        
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
