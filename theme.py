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
    font-size: 12pt;
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
    font-size: 9pt;
}

QLabel#title_label {
    font-size: 14pt;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 10px;
}

/* ComboBox Styling */
QComboBox {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 8px;
    padding: 15px 20px;
    color: #ffffff;
    font-size: 12pt;
    min-height: 35px;
    max-height: 50px;
}

QComboBox:hover {
    border-color: #0078d4;
    background-color: #454545;
}

QComboBox:focus {
    border-color: #0078d4;
    background-color: #454545;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
    background-color: transparent;
}

QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid #cccccc;
    margin-right: 8px;
}

QComboBox::down-arrow:hover {
    border-top-color: #ffffff;
}

QComboBox QAbstractItemView {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 6px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    color: #ffffff;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    height: 40px;
    padding: 8px 12px;
    border-radius: 4px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #555555;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #0078d4;
}

/* Button Styling */
QPushButton {
    background-color: #0078d4;
    border: none;
    border-radius: 8px;
    color: #ffffff;
    font-weight: 600;
    padding: 15px 30px;
    font-size: 12pt;
    min-height: 35px;
    max-height: 55px;
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

/* Mute Button Special Styling */
QPushButton#mute_button {
    background-color: #2d5d2d;
    font-size: 13pt;
    min-width: 180px;
}

QPushButton#mute_button:hover {
    background-color: #3d7d3d;
}

QPushButton#mute_button:pressed {
    background-color: #1d4d1d;
}

QPushButton#mute_button[muted="true"] {
    background-color: #7d2d2d;
}

QPushButton#mute_button[muted="true"]:hover {
    background-color: #9d3d3d;
}

QPushButton#mute_button[muted="true"]:pressed {
    background-color: #5d1d1d;
}

/* Refresh Button */
QPushButton#refresh_button {
    background-color: #666666;
    min-width: 50px;
    font-size: 16pt;
}

QPushButton#refresh_button:hover {
    background-color: #777777;
}

QPushButton#refresh_button:pressed {
    background-color: #555555;
}

/* Status Indicator */
QFrame#status_indicator {
    background-color: #666666;
    border: 2px solid #888888;
    border-radius: 8px;
    min-width: 12px;
    max-width: 12px;
    min-height: 12px;
    max-height: 12px;
}

QFrame#status_indicator[status="streaming"] {
    background-color: #00cc00;
    border-color: #00aa00;
}

QFrame#status_indicator[status="error"] {
    background-color: #ff4444;
    border-color: #cc0000;
}

QFrame#status_indicator[status="stopped"] {
    background-color: #666666;
    border-color: #888888;
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
"""

def apply_theme(app):
    """Apply the dark theme to the application"""
    app.setStyleSheet(DARK_THEME)
