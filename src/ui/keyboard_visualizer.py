from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtCore import Qt, QSize

from src.core.settings_manager import SettingsManager

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
        active_color = QColor(*self.settings_manager.get_gradient_config()["colors"][2])
        painter = QPainter(self)
        key_width = self.width() / 88
        key_height = self.height()

        # Adjust for standard 88-key piano starting at A
        black_keys = {1, 4, 6, 9, 11, 13, 16, 18, 21, 23, 25, 28, 30, 33, 35, 37, 40, 42, 45, 47, 49, 52, 54, 57, 59, 61, 64, 66, 69, 71, 73, 76, 78, 81, 83, 85}

        # Define the roundness as an adjustable variable
        corner_radius = 8 

        painter.setRenderHint(QPainter.Antialiasing)

        # Define the clipping region as a rounded rectangle with only bottom corners rounded
        clipping_path = QPainterPath()
        clipping_path.moveTo(0, 0)
        clipping_path.lineTo(self.width(), 0)
        clipping_path.lineTo(self.width(), self.height() - corner_radius)
        clipping_path.quadTo(self.width(), self.height(), self.width() - corner_radius, self.height())
        clipping_path.lineTo(corner_radius, self.height())
        clipping_path.quadTo(0, self.height(), 0, self.height() - corner_radius)
        clipping_path.lineTo(0, 0)
        painter.setClipPath(clipping_path)

        for i in range(88):
            if i % 12 in black_keys:
                if self.key_states[i]:
                    painter.setBrush(active_color)  # Red for active black keys
                else:
                    painter.setBrush(QColor(0, 0, 0))  # Black for inactive black keys
            else:
                if self.key_states[i]:
                    painter.setBrush(active_color)  # Red for active white keys
                else:
                    painter.setBrush(QColor(255, 255, 255))  # White for inactive white keys

            painter.setPen(Qt.black)
            painter.drawRect(i * key_width, 0, key_width, key_height)

        painter.end()
