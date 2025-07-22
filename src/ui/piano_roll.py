from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QFont
import time
from typing import Dict, List, Tuple


class PianoRollWidget(QWidget):
    """Piano roll waterfall visualization showing MIDI notes over time"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Piano constants
        self.NUM_KEYS = 88  # Standard piano has 88 keys
        self.LOWEST_NOTE = 21  # A0 (MIDI note 21)
        self.HIGHEST_NOTE = 108  # C8 (MIDI note 108)
        
        # Visual settings
        self.SCROLL_SPEED = 100  # pixels per second
        self.NOTE_HEIGHT = 3.0  # Height of note rectangles
        self.WATERFALL_LENGTH = 5.0  # seconds of history to show
        self.KEY_WIDTH_MIN = 5  # Minimum key width for better visibility
        
        # Active notes tracking
        self.active_notes: Dict[int, Tuple[float, int]] = {}  # note -> (start_time, velocity)
        self.note_history: List[Tuple[int, float, float, int, float]] = []  # (note, start_time, end_time, velocity, visual_length)
        
        # Colors for different velocities (brighter colors for better visibility)
        self.velocity_colors = [
            QColor(100, 170, 255),  # Light blue for soft notes
            QColor(80, 140, 255),   # Royal blue
            QColor(50, 170, 255),   # Dodger blue
            QColor(0, 210, 255),    # Deep sky blue
            QColor(0, 255, 255),    # Cyan for medium notes
            QColor(50, 255, 50),    # Lime green
            QColor(255, 255, 0),    # Yellow
            QColor(255, 180, 0),    # Orange
            QColor(255, 100, 0),    # Red orange for loud notes
            QColor(255, 50, 50),    # Red for very loud notes
        ]
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        # Track current time
        self.start_time = time.time()
        self.last_debug_time = 0
        
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def note_to_key_index(self, midi_note: int) -> int:
        """Convert MIDI note number to piano key index (0-87)"""
        return max(0, min(87, midi_note - self.LOWEST_NOTE))
    
    def key_index_to_x(self, key_index: int, widget_width: int) -> float:
        """Convert key index to x coordinate"""
        # More even spacing for better visualization
        key_width = max(self.KEY_WIDTH_MIN, widget_width / self.NUM_KEYS)
        return key_index * key_width
    
    def key_width(self, widget_width: int) -> float:
        """Get the width of a key based on widget width"""
        return max(self.KEY_WIDTH_MIN, widget_width / self.NUM_KEYS)
    
    def is_black_key(self, midi_note: int) -> bool:
        """Check if a MIDI note corresponds to a black key"""
        note_in_octave = midi_note % 12
        return note_in_octave in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
    
    def velocity_to_color(self, velocity: int) -> QColor:
        """Convert MIDI velocity to color"""
        # Map velocity (0-127) to color index
        color_index = min(9, velocity // 13)
        return self.velocity_colors[color_index]
    
    def add_note_on(self, note: int, velocity: int):
        """Handle note on event"""
        if self.LOWEST_NOTE <= note <= self.HIGHEST_NOTE:
            current_time = time.time()
            self.active_notes[note] = (current_time, velocity)
            self.update()  # Force immediate repaint
    
    def add_note_off(self, note: int):
        """Handle note off event"""
        if note in self.active_notes:
            start_time, velocity = self.active_notes[note]
            end_time = time.time()
            
            # Add to history
            self.note_history.append((note, start_time, end_time, velocity))
            
            # Remove from active notes
            del self.active_notes[note]
            self.update()  # Force immediate repaint
    
    def clear_notes(self):
        """Clear all notes and history"""
        self.active_notes.clear()
        self.note_history.clear()
        self.update()  # Force immediate repaint
    
    def paintEvent(self, event):
        """Paint the piano roll waterfall"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        widget_width = self.width()
        widget_height = self.height()
        current_time = time.time()
        
        # Clear background
        painter.fillRect(self.rect(), QColor(20, 20, 20))
        
        # Draw a border to see if this widget is displayed
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
        # Draw piano key guides with white/black key visualization
        key_width = self.key_width(widget_width)
        
        # Draw white keys first (background)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            x = self.key_index_to_x(i, widget_width)
            
            if not self.is_black_key(midi_note):
                # Draw white key
                painter.setBrush(QBrush(QColor(40, 40, 40)))
                painter.drawRect(QRectF(x, 0, key_width, widget_height))
        
        # Draw black keys (overlay)
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            x = self.key_index_to_x(i, widget_width)
            
            if self.is_black_key(midi_note):
                # Draw black key
                painter.setBrush(QBrush(QColor(20, 20, 20)))
                painter.drawRect(QRectF(x, 0, key_width, widget_height))
        
        # Draw octave separators for C notes
        painter.setPen(QPen(QColor(100, 100, 100)))
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            note_in_octave = midi_note % 12
            if note_in_octave == 0:  # C notes
                x = self.key_index_to_x(i, widget_width)
                painter.drawLine(x, 0, x, widget_height)
        
        # Draw debugging text if no notes are active
        if not self.active_notes and not self.note_history:
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.setFont(QFont("Arial", 11))
            text = "Piano Roll Active\nPlay MIDI notes or double-click to test"
            painter.drawText(self.rect().adjusted(20, 20, -20, -20), 
                            Qt.AlignmentFlag.AlignCenter, text)
        
        # Calculate time window
        time_window_start = current_time - self.WATERFALL_LENGTH
        
        # Remove old notes from history
        self.note_history = [note for note in self.note_history 
                           if note[2] > time_window_start]  # end_time > window_start
        
        # Draw completed notes from history (these move upward as fixed rectangles)
        for note, start_time, end_time, velocity in self.note_history:
            if start_time < current_time and end_time > time_window_start:
                self._draw_completed_note_rectangle(painter, note, start_time, end_time, 
                                                  velocity, current_time, widget_width, widget_height)
        
        # Draw active notes (these grow upward from the bottom)
        for note, (start_time, velocity) in self.active_notes.items():
            if start_time < current_time:
                self._draw_active_note_rectangle(painter, note, start_time, 
                                               velocity, current_time, widget_width, widget_height)
        
        # Draw debug info about active notes (simplified)
        if self.active_notes or self.note_history:
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.setFont(QFont("Arial", 8))
            active_notes_text = f"Active: {len(self.active_notes)} | History: {len(self.note_history)}"
            painter.drawText(10, 15, active_notes_text)
    
    def _draw_active_note_rectangle(self, painter: QPainter, note: int, start_time: float, 
                                  velocity: int, current_time: float, 
                                  widget_width: int, widget_height: int):
        """Draw an active note rectangle that grows upward from the bottom"""
        # Calculate position
        key_index = self.note_to_key_index(note)
        key_width = self.key_width(widget_width)
        x = self.key_index_to_x(key_index, widget_width)
        
        # Calculate how long the note has been playing
        note_duration = current_time - start_time
        
        # Y positions - active notes start at the bottom and grow upward
        y_bottom = widget_height  # Bottom of the widget
        y_top = widget_height - (note_duration * self.SCROLL_SPEED)  # Top grows upward based on duration
        
        # Ensure the top doesn't go above the widget
        y_top = max(0, y_top)
        
        # Calculate rectangle dimensions
        rect_height = y_bottom - y_top
        
        # Skip if no height (shouldn't happen for active notes)
        if rect_height <= 0:
            return
        
        # Get color based on velocity (make it brighter for active notes)
        base_color = self.velocity_to_color(velocity)
        color = QColor(
            min(255, base_color.red() + 50),    # Extra bright for active notes
            min(255, base_color.green() + 50),
            min(255, base_color.blue() + 50),
            220  # Slightly more opaque for active notes
        )
        
        # Create rect with slight inset for visibility
        rect_width = max(10, key_width * 0.9)
        x_center = x + (key_width / 2)
        rect = QRectF(x_center - (rect_width / 2), y_top, rect_width, rect_height)
        
        # Draw with a thicker border for active notes
        painter.setPen(QPen(Qt.GlobalColor.yellow, 2))  # Yellow border for active notes
        
        # Draw the note rectangle with a gradient fill
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(120))
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners
        painter.drawRoundedRect(rect, 3, 3)
        
        # Draw note number inside if rectangle is big enough
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        if rect_height > 14 and rect_width > 14:
            text_rect = rect.adjusted(2, 2, -2, -2)
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = (note - 12) // 12
            note_name = note_names[(note - 12) % 12]
            display_text = f"{note_name}{octave}"
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)

    def _draw_completed_note_rectangle(self, painter: QPainter, note: int, start_time: float, 
                                     end_time: float, velocity: int, current_time: float, 
                                     widget_width: int, widget_height: int):
        """Draw a completed note rectangle that moves upward as a fixed-size rectangle"""
        # Calculate position
        key_index = self.note_to_key_index(note)
        key_width = self.key_width(widget_width)
        x = self.key_index_to_x(key_index, widget_width)
        
        # Calculate time-based y positions (waterfall moves up)
        time_elapsed_start = current_time - start_time
        time_elapsed_end = current_time - end_time
        
        # Y positions (notes scroll upward)
        y_start = widget_height - (time_elapsed_start * self.SCROLL_SPEED)
        y_end = widget_height - (time_elapsed_end * self.SCROLL_SPEED)
        
        # Skip if completely outside visible area
        if y_end > widget_height or y_start < 0:
            return
        
        # Clamp to visible area
        y_start = max(0, min(widget_height, y_start))
        y_end = max(0, min(widget_height, y_end))
        
        # Calculate rectangle dimensions
        rect_height = max(5, y_start - y_end)  # Ensure at least 5 pixels high for visibility
        
        # Get color based on velocity (normal brightness for completed notes)
        base_color = self.velocity_to_color(velocity)
        color = QColor(
            min(255, base_color.red() + 30),
            min(255, base_color.green() + 30),
            min(255, base_color.blue() + 30),
            240  # Make slightly transparent
        )
        
        # Create rect with slight inset for visibility
        rect_width = max(10, key_width * 0.9)
        x_center = x + (key_width / 2)
        rect = QRectF(x_center - (rect_width / 2), y_end, rect_width, rect_height)
        
        # Draw a border around the note - use white for visibility
        painter.setPen(QPen(Qt.GlobalColor.white, 1.5))
        
        # Draw the note rectangle with a gradient fill
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(110))
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners for better appearance
        painter.drawRoundedRect(rect, 3, 3)
        
        # Draw note number inside
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        # Only draw text if rectangle is big enough
        if rect_height > 14 and rect_width > 14:
            text_rect = rect.adjusted(2, 2, -2, -2)  # Small inset for text
            # Show note name (C4, D4, etc.) instead of MIDI number
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = (note - 12) // 12
            note_name = note_names[(note - 12) % 12]
            display_text = f"{note_name}{octave}"
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)
    
    def _draw_active_note_rectangle(self, painter: QPainter, note: int, start_time: float, 
                                  velocity: int, current_time: float, 
                                  widget_width: int, widget_height: int):
        """Draw an active note rectangle that grows upward from the bottom"""
        # Calculate position
        key_index = self.note_to_key_index(note)
        key_width = self.key_width(widget_width)
        x = self.key_index_to_x(key_index, widget_width)
        
        # Calculate how long the note has been playing
        note_duration = current_time - start_time
        
        # Y positions - active notes start at the bottom and grow upward
        y_bottom = widget_height  # Bottom of the widget
        y_top = widget_height - (note_duration * self.SCROLL_SPEED)  # Top grows upward based on duration
        
        # Ensure the top doesn't go above the widget
        y_top = max(0, y_top)
        
        # Calculate rectangle dimensions
        rect_height = y_bottom - y_top
        
        # Skip if no height (shouldn't happen for active notes)
        if rect_height <= 0:
            return
        
        # Get color based on velocity (make it brighter for active notes)
        base_color = self.velocity_to_color(velocity)
        color = QColor(
            min(255, base_color.red() + 50),    # Extra bright for active notes
            min(255, base_color.green() + 50),
            min(255, base_color.blue() + 50),
            220  # Slightly more opaque for active notes
        )
        
        # Create rect with slight inset for visibility
        rect_width = max(10, key_width * 0.9)
        x_center = x + (key_width / 2)
        rect = QRectF(x_center - (rect_width / 2), y_top, rect_width, rect_height)
        
        # Draw with a thicker border for active notes
        painter.setPen(QPen(Qt.GlobalColor.yellow, 2))  # Yellow border for active notes
        
        # Draw the note rectangle with a gradient fill
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(120))
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners
        painter.drawRoundedRect(rect, 3, 3)
        
        # Draw note number inside if rectangle is big enough
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        if rect_height > 14 and rect_width > 14:
            text_rect = rect.adjusted(2, 2, -2, -2)
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = (note - 12) // 12
            note_name = note_names[(note - 12) % 12]
            display_text = f"{note_name}{octave}"
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)

    def _draw_completed_note_rectangle(self, painter: QPainter, note: int, start_time: float, 
                                     end_time: float, velocity: int, current_time: float, 
                                     widget_width: int, widget_height: int):
        """Draw a completed note rectangle (static, moves up with time)"""
        # Calculate position
        key_index = self.note_to_key_index(note)
        
        # Get key width - ensure it's visible
        key_width = self.key_width(widget_width)
        
        # Calculate x position
        x = self.key_index_to_x(key_index, widget_width)
        
        # Calculate time-based y positions (waterfall moves up)
        time_elapsed_start = current_time - start_time
        time_elapsed_end = current_time - end_time
        
        # Y positions (notes scroll upward)
        y_start = widget_height - (time_elapsed_start * self.SCROLL_SPEED)
        y_end = widget_height - (time_elapsed_end * self.SCROLL_SPEED)
        
        # Skip if completely outside visible area
        if y_end > widget_height or y_start < 0:
            return
        
        # Clamp to visible area
        y_start = max(0, min(widget_height, y_start))
        y_end = max(0, min(widget_height, y_end))
        
        # Calculate rectangle dimensions
        rect_height = max(5, y_start - y_end)  # Ensure at least 5 pixels high for visibility
        
        # Get color based on velocity (make it brighter)
        base_color = self.velocity_to_color(velocity)
        color = QColor(
            min(255, base_color.red() + 30),
            min(255, base_color.green() + 30),
            min(255, base_color.blue() + 30),
            240  # Make slightly transparent
        )
        
        # Create rect with slight inset for visibility
        rect_width = max(10, key_width * 0.9)  # Ensure at least 10 pixels wide
        x_center = x + (key_width / 2)
        rect = QRectF(x_center - (rect_width / 2), y_end, rect_width, rect_height)
        
        # Draw a border around the note - use white for visibility
        painter.setPen(QPen(Qt.GlobalColor.white, 1.5))
        
        # Draw the note rectangle with a gradient fill
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(110))
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners for better appearance
        painter.drawRoundedRect(rect, 3, 3)
        
        # Draw note number inside
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        # Only draw text if rectangle is big enough
        if rect_height > 14 and rect_width > 14:
            text_rect = rect.adjusted(2, 2, -2, -2)  # Small inset for text
            # Show note name (C4, D4, etc.) instead of MIDI number
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = (note - 12) // 12
            note_name = note_names[(note - 12) % 12]
            display_text = f"{note_name}{octave}"
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_text)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks (for testing)"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate which key was clicked for testing
            key_index = int((event.x() / self.width()) * self.NUM_KEYS)
            midi_note = key_index + self.LOWEST_NOTE
            
            # Simulate note on/off for testing
            import random
            velocity = random.randint(40, 127)
            self.add_note_on(midi_note, velocity)
            
            # Auto note-off after 1 second for testing
            QTimer.singleShot(1000, lambda: self.add_note_off(midi_note))
    
    def test_piano_roll(self):
        """Test method to add some notes for debugging"""
        self.clear_notes()
        
        # Play a simple C major chord
        chord_notes = [60, 64, 67]  # C4, E4, G4
        
        # Add the chord
        for i, note in enumerate(chord_notes):
            QTimer.singleShot(i * 100, lambda n=note, v=80: self.add_note_on(n, v))
            # Schedule note off after 2 seconds
            QTimer.singleShot(2000 + i * 100, lambda n=note: self.add_note_off(n))
