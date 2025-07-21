"""
Dark theme stylesheet for the Audio Streamer application
"""

DARK_THEME = """
/* Main Application Style */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QWidget {
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

/* Frame and Container Styling */
QFrame {
    background-color: #363636;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 10px;
}

QFrame#main_frame {
    background-color: #2b2b2b;
    border: none;
    border-radius: 0px;
}

/* Label Styling */
QLabel {
    background-color: transparent;
    color: #ffffff;
    font-weight: 500;
}

QLabel#status_label {
    color: #cccccc;
    font-size: 8pt;
    margin: 0px;
}

QLabel#title_label {
    font-size: 14pt;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 10px;
}

/* ComboBox Styling - Modern minimal design with no dropdown arrow */
QComboBox {
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

QComboBox:hover {
    border-color: #0078d4;
    background-color: #454545;
}

QComboBox:focus {
    border-color: #0078d4;
    background-color: #454545;
    outline: none;
}

/* Completely remove dropdown button for minimal design */
QComboBox::drop-down {
    border: none;
    background: transparent;
    width: 0px;
}

/* Hide the arrow completely */
QComboBox::down-arrow {
    image: none;
    border: none;
    width: 0px;
    height: 0px;
}

/* Style the dropdown list */
QComboBox QAbstractItemView {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 6px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    color: #ffffff;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    height: 28px;
    padding: 4px 8px;
    border-radius: 2px;
    border: none;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #555555;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #0078d4;
}

/* Custom scrollbar for dropdown - fully rounded (pill-shaped) */
QComboBox QAbstractItemView QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
    border-radius: 6px;
}

QComboBox QAbstractItemView QScrollBar::handle:vertical {
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

QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QComboBox QAbstractItemView QScrollBar::handle:vertical:pressed {
    background-color: #777777;
}

QComboBox QAbstractItemView QScrollBar::add-line:vertical,
QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QComboBox QAbstractItemView QScrollBar::add-page:vertical,
QComboBox QAbstractItemView QScrollBar::sub-page:vertical {
    background-color: transparent;
}

/* Button Styling */
QPushButton {
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

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Status/Mute Button - Green when streaming, Red when muted */
QPushButton#status_mute_button {
    background-color: #2d7d2d;
    font-size: 9pt;
    font-weight: 600;
    min-width: 80px;
    max-width: 80px;
    padding: 4px 8px;
}

QPushButton#status_mute_button:hover {
    background-color: #3d9d3d;
}

QPushButton#status_mute_button:pressed {
    background-color: #1d6d1d;
}

QPushButton#status_mute_button[muted="true"] {
    background-color: #7d2d2d;
}

QPushButton#status_mute_button[muted="true"]:hover {
    background-color: #9d3d3d;
}

QPushButton#status_mute_button[muted="true"]:pressed {
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
    app.setStyleSheet(DARK_THEME)
