"""
Dark theme stylesheet for the Audio Streamer application
"""

DARK_THEME = """
/* Main Application Style */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* Scope to MainWindow to avoid affecting third-party dialogs */
QMainWindow QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
}

/* Custom Title Bar Styling */
CustomTitleBar {
    background-color: #363636;
    border: none;
}

CustomTitleBar QLabel {
    color: #ffffff;
    background-color: transparent;
    border: none;
}

CustomTitleBar QPushButton#title_button {
    background-color: transparent;
    border: none;
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
    border-radius: 0px;
    text-align: center;
}

CustomTitleBar QPushButton#title_button:hover {
    background-color: #555555;
}

CustomTitleBar QPushButton#title_button:pressed {
    background-color: #666666;
}

CustomTitleBar QPushButton#close_button {
    background-color: transparent;
    border: none;
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
    border-radius: 0px;
    text-align: center;
}

CustomTitleBar QPushButton#close_button:hover {
    background-color: #e74c3c;
}

CustomTitleBar QPushButton#close_button:pressed {
    background-color: #c0392b;
}

/* Frame and Container Styling - Scope to MainWindow */
QMainWindow QFrame {
    background-color: #363636;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 10px;
}

QMainWindow QFrame#main_frame {
    background-color: #2b2b2b;
    border: none;
    border-radius: 0px;
}

/* Label Styling - Scope to MainWindow */
QMainWindow QLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: 500;
}

QMainWindow QLabel#status_label {
    color: #cccccc;
    font-size: 8pt;
    margin: 0px;
}

QMainWindow QLabel#title_label {
    font-size: 14pt;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 10px;
}

/* ComboBox Styling - Modern minimal design with no dropdown arrow - Scope to MainWindow */
QMainWindow QComboBox {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 9pt;
    min-height: 18px;
    max-height: 30px;
    /* Remove 3D effects */
    border-style: solid;
    outline: none;
}

QMainWindow QComboBox:hover {
    border-color: #0078d4;
    background-color: #454545;
}

QMainWindow QComboBox:focus {
    border-color: #0078d4;
    background-color: #454545;
    outline: none;
}

/* Completely remove dropdown button for minimal design */
QMainWindow QComboBox::drop-down {
    border: none;
    background: transparent;
    width: 0px;
}

/* Hide the arrow completely */
QMainWindow QComboBox::down-arrow {
    image: none;
    border: none;
    width: 0px;
    height: 0px;
}

/* Style the dropdown list */
QMainWindow QComboBox QAbstractItemView {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 6px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    color: #ffffff;
    padding: 4px;
    outline: none;
}

QMainWindow QComboBox QAbstractItemView::item {
    height: 28px;
    padding: 4px 8px;
    border-radius: 2px;
    border: none;
}

QMainWindow QComboBox QAbstractItemView::item:hover {
    background-color: #555555;
}

QMainWindow QComboBox QAbstractItemView::item:selected {
    background-color: #0078d4;
}

/* Custom scrollbar for dropdown - fully rounded (pill-shaped) */
QMainWindow QComboBox QAbstractItemView QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
    border-radius: 6px;
}

QMainWindow QComboBox QAbstractItemView QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
    /* Make it fully pill-shaped by ensuring radius covers the full width */
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border-bottom-left-radius: 6px;
    border-bottom-right-radius: 6px;
}

QMainWindow QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QMainWindow QComboBox QAbstractItemView QScrollBar::handle:vertical:pressed {
    background-color: #777777;
}

QMainWindow QComboBox QAbstractItemView QScrollBar::add-line:vertical,
QMainWindow QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QMainWindow QComboBox QAbstractItemView QScrollBar::add-page:vertical,
QMainWindow QComboBox QAbstractItemView QScrollBar::sub-page:vertical {
    background-color: transparent;
}

/* Button Styling - Scope to MainWindow */
QMainWindow QPushButton {
    background-color: #0078d4;
    border: none;
    border-radius: 4px;
    color: #ffffff;
    font-weight: 600;
    padding: 6px 10px;
    font-size: 9pt;
    min-height: 18px;
    max-height: 30px;
}

QMainWindow QPushButton:hover {
    background-color: #106ebe;
}

QMainWindow QPushButton:pressed {
    background-color: #005a9e;
}

QMainWindow QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Status/Mute Button - Green when streaming, Red when muted */
QMainWindow QPushButton#status_mute_button {
    background-color: #2d7d2d;
    font-size: 9pt;
    font-weight: 600;
    min-width: 80px;
    max-width: 80px;
    padding: 4px 8px;
}

QMainWindow QPushButton#status_mute_button:hover {
    background-color: #3d9d3d;
}

QMainWindow QPushButton#status_mute_button:pressed {
    background-color: #1d6d1d;
}

QMainWindow QPushButton#status_mute_button[muted="true"] {
    background-color: #7d2d2d;
}

QMainWindow QPushButton#status_mute_button[muted="true"]:hover {
    background-color: #9d3d3d;
}

QMainWindow QPushButton#status_mute_button[muted="true"]:pressed {
    background-color: #5d1d1d;
}

/* Spacing and Layout */
QVBoxLayout {
    spacing: 10px;
}

QHBoxLayout {
    spacing: 10px;
}

/* Tooltip Styling */
QToolTip {
    background-color: #404040;
    color: #ffffff;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 6px;
    font-size: 9pt;
}

/* Spectrum Analyzer Styling */
SpectrumAnalyzer {
    background-color: #2b2b2b;
    border: none;
    border-radius: 0px;
    margin: 4px;
}
"""

def apply_theme(app):
    """Apply the dark theme to the application"""
    import platform
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
    
    # Apply the stylesheet
    app.setStyleSheet(DARK_THEME)
    
    # Set a dark palette for better integration with system theme
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    
    # Base colors (for input fields, etc.)
    palette.setColor(QPalette.ColorRole.Base, QColor(60, 60, 60))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(74, 74, 74))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(85, 85, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Link colors
    palette.setColor(QPalette.ColorRole.Link, QColor(85, 170, 255))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(255, 85, 255))
    
    # Apply the palette
    app.setPalette(palette)
    
    # On Windows, try to enable dark mode for the title bar
    if platform.system() == "Windows":
        try:
            import ctypes
            from ctypes import wintypes
            
            # Try to enable dark mode for the application
            # This uses the DwmSetWindowAttribute API to set DWMWA_USE_IMMERSIVE_DARK_MODE
            def enable_dark_title_bar(hwnd):
                try:
                    # Define constants
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    
                    # Load dwmapi.dll
                    dwmapi = ctypes.windll.dwmapi
                    
                    # Set up the function
                    dwmapi.DwmSetWindowAttribute.argtypes = [
                        wintypes.HWND,
                        wintypes.DWORD,
                        ctypes.POINTER(wintypes.BOOL),
                        wintypes.DWORD
                    ]
                    
                    # Enable dark mode
                    use_dark_mode = wintypes.BOOL(True)
                    dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_USE_IMMERSIVE_DARK_MODE,
                        ctypes.byref(use_dark_mode),
                        ctypes.sizeof(use_dark_mode)
                    )
                except Exception:
                    pass  # Silently fail if not supported
            
            # Store the function so it can be called later when windows are created
            app.enable_dark_title_bar = enable_dark_title_bar
            
        except ImportError:
            pass  # ctypes not available
