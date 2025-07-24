from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtCore import Qt, QSize

from src.core.settings_manager import SettingsManager
from src.ui.piano_layout import PianoLayout
from src.ui.piano_roll import DEFAULT_GRADIENT_CONFIG

class KeyboardVisualizer(QWidget):
    def __init__(self, parent=None, settings_manager: SettingsManager=None):
        super().__init__(parent)

        self.settings_manager = settings_manager

        self.setMinimumSize(QSize(600, 80))
        self.setMaximumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Initialize key states (88 keys for a standard piano)
        self.key_states = [False] * 88

    def highlight_key_on(self, midi_note):
        """Highlight a key when a MIDI note is pressed."""
        key_index = midi_note - 21  # MIDI note 21 corresponds to A0
        if 0 <= key_index < len(self.key_states):
            self.key_states[key_index] = True
            self.update()

    def highlight_key_off(self, midi_note):
        """Unhighlight a key when a MIDI note is released."""
        key_index = midi_note - 21
        if 0 <= key_index < len(self.key_states):
            self.key_states[key_index] = False
            self.update()

    def paintEvent(self, event):
        """Custom paint event to draw the keyboard."""
        gradient_config = { **DEFAULT_GRADIENT_CONFIG, **self.settings_manager.get_gradient_config() }
        active_color = QColor(*gradient_config["colors"][2])
        painter = QPainter(self)
        
        total_width = self.width()
        key_height = self.height()

        # Define the roundness as an adjustable variable
        corner_radius = 8 

        painter.setRenderHint(QPainter.Antialiasing)

        # Define the clipping region as a rounded rectangle with only bottom corners rounded
        clipping_path = QPainterPath()
        clipping_path.moveTo(0, 0)
        clipping_path.lineTo(total_width, 0)
        clipping_path.lineTo(total_width, key_height - corner_radius)
        clipping_path.quadTo(total_width, key_height, total_width - corner_radius, key_height)
        clipping_path.lineTo(corner_radius, key_height)
        clipping_path.quadTo(0, key_height, 0, key_height - corner_radius)
        clipping_path.lineTo(0, 0)
        painter.setClipPath(clipping_path)

        # Get all key information using the piano layout system
        all_key_info = PianoLayout.get_all_key_info(total_width)
        
        # Draw white keys first (background layer)
        painter.setPen(Qt.black)
        for i, key_info in enumerate(all_key_info):
            if not key_info.is_black:  # White keys
                if self.key_states[i]:
                    painter.setBrush(active_color)
                else:
                    painter.setBrush(QColor(255, 255, 255))
                
                painter.drawRect(key_info.x, 0, key_info.width, key_height)
        
        # Draw black keys second (overlay layer)
        black_key_height = key_height * PianoLayout.BLACK_KEY_HEIGHT_RATIO
        for i, key_info in enumerate(all_key_info):
            if key_info.is_black:  # Black keys
                if self.key_states[i]:
                    painter.setBrush(active_color)
                else:
                    painter.setBrush(QColor(0, 0, 0))
                
                painter.drawRect(key_info.x, 0, key_info.width, black_key_height)

        painter.end()
