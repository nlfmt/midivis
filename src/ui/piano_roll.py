from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QFont, QPainterPath
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
        
        # Pause functionality
        self.is_paused = False
        self.pause_start_time = 0.0  # When the pause started
        self.total_pause_duration = 0.0  # Total time spent paused
        
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
        # Remove the stylesheet to avoid background conflicts
        # self.setStyleSheet("""
        #     background-color: #1a1a1a;
        #     border-radius: 8px;
        # """)
    
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
            # Use adjusted time that accounts for pause durations
            if self.is_paused:
                current_time = self.pause_start_time - self.total_pause_duration
            else:
                current_time = time.time() - self.total_pause_duration
            self.active_notes[note] = (current_time, velocity)
            self.update()  # Force immediate repaint
    
    def add_note_off(self, note: int):
        """Handle note off event"""
        if note in self.active_notes:
            start_time, velocity = self.active_notes[note]
            
            # Use adjusted time that accounts for pause durations
            if self.is_paused:
                end_time = self.pause_start_time - self.total_pause_duration
            else:
                end_time = time.time() - self.total_pause_duration
            
            # Calculate the visual length the note had when it was active
            note_duration = end_time - start_time
            visual_length = note_duration * self.SCROLL_SPEED
            
            # Add to history with the visual length preserved
            self.note_history.append((note, start_time, end_time, velocity, visual_length))
            
            # Remove from active notes
            del self.active_notes[note]
            self.update()  # Force immediate repaint
    
    def clear_notes(self):
        """Clear all notes and history"""
        self.active_notes.clear()
        self.note_history.clear()
        self.update()  # Force immediate repaint
    
    def pause(self):
        """Pause the piano roll animation"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
    
    def play(self):
        """Resume the piano roll animation"""
        if self.is_paused:
            self.is_paused = False
            # Add the time we were paused to the total pause duration
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_duration += pause_duration
    
    def toggle_pause(self):
        """Toggle pause/play state"""
        if self.is_paused:
            self.play()
        else:
            self.pause()
    
    def is_playing(self):
        """Check if the piano roll is currently playing (not paused)"""
        return not self.is_paused
    
    def paintEvent(self, event):
        """Paint the piano roll waterfall"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        widget_width = self.width()
        widget_height = self.height()
        
        # Handle paused state for time calculation
        if self.is_paused:
            # While paused, use the time when we paused minus any previous pause durations
            current_time = self.pause_start_time - self.total_pause_duration
        else:
            # While playing, use current time minus all pause durations
            current_time = time.time() - self.total_pause_duration
        
        # Clear the entire widget with transparent background first
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        # Draw rounded background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRoundedRect(QRectF(self.rect()), 8, 8)
        
        # Create rounded rectangle path for clipping content
        content_rect = QRectF(self.rect())
        content_path = QPainterPath()
        content_path.addRoundedRect(content_rect, 8, 8)
        
        # Set clipping path for rounded corners
        painter.setClipPath(content_path)
        
        # Draw piano key guides with white/black key visualization
        key_width = self.key_width(widget_width)
        
        # Draw white keys first (background)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            x = self.key_index_to_x(i, widget_width)
            
            if not self.is_black_key(midi_note):
                # Draw white key - much darker and more subtle
                painter.setBrush(QBrush(QColor(25, 25, 25)))
                painter.drawRect(QRectF(x, 0, key_width, widget_height))
        
        # Draw black keys (overlay)
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            x = self.key_index_to_x(i, widget_width)
            
            if self.is_black_key(midi_note):
                # Draw black key - slightly darker than background
                painter.setBrush(QBrush(QColor(18, 18, 18)))
                painter.drawRect(QRectF(x, 0, key_width, widget_height))
        
        # Draw octave separators for C notes - much more subtle
        painter.setPen(QPen(QColor(35, 35, 35)))
        for i in range(self.NUM_KEYS):
            midi_note = i + self.LOWEST_NOTE
            note_in_octave = midi_note % 12
            if note_in_octave == 0:  # C notes
                x = self.key_index_to_x(i, widget_width)
                painter.drawLine(x, 0, x, widget_height)
        
        # Remove old notes from history - only remove when they're completely above the widget
        self.note_history = [note_data for note_data in self.note_history 
                           if self._note_still_visible(note_data, current_time, widget_height)]
        
        # Draw completed notes from history (these move upward as fixed rectangles)
        for note, start_time, end_time, velocity, visual_length in self.note_history:
            self._draw_completed_note_rectangle(painter, note, start_time, end_time, 
                                              velocity, visual_length, current_time, widget_width, widget_height)
        
        # Draw active notes (these grow upward from the bottom)
        for note, (start_time, velocity) in self.active_notes.items():
            if start_time < current_time:
                self._draw_active_note_rectangle(painter, note, start_time, 
                                               velocity, current_time, widget_width, widget_height)
    
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
        
        # Draw with a white border for active notes
        painter.setPen(QPen(Qt.GlobalColor.white, 1))  # White border, 1 pixel width
        
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
                                     end_time: float, velocity: int, visual_length: float, current_time: float, 
                                     widget_width: int, widget_height: int):
        """Draw a completed note rectangle that moves upward with preserved length"""
        # Calculate position
        key_index = self.note_to_key_index(note)
        key_width = self.key_width(widget_width)
        x = self.key_index_to_x(key_index, widget_width)
        
        # Calculate how much time has elapsed since the note ended
        time_since_end = current_time - end_time
        
        # The bottom of the rectangle moves upward based on how long ago the note ended
        y_bottom = widget_height - (time_since_end * self.SCROLL_SPEED)
        # The top is offset by the preserved visual length
        y_top = y_bottom - visual_length
        
        # Only skip if the BOTTOM of the note is completely above the widget
        # This means the entire note has scrolled out of view
        if y_bottom < 0:
            return
        
        # For drawing, clamp coordinates to visible area
        y_bottom_draw = max(0, min(widget_height, y_bottom))
        y_top_draw = max(0, min(widget_height, y_top))
        
        # Calculate rectangle dimensions for drawing
        rect_height = y_bottom_draw - y_top_draw
        
        # Skip only if there's nothing to draw after clamping
        if rect_height <= 0:
            return
        
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
        rect = QRectF(x_center - (rect_width / 2), y_top_draw, rect_width, rect_height)
        
        # No border for completed notes - just the solid color
        painter.setPen(Qt.PenStyle.NoPen)
        
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
    
    def _note_still_visible(self, note_data: Tuple[int, float, float, int, float], 
                          current_time: float, widget_height: int) -> bool:
        """Check if a completed note is still visible in the widget"""
        note, start_time, end_time, velocity, visual_length = note_data
        
        # Calculate how much time has elapsed since the note ended
        time_since_end = current_time - end_time
        
        # The bottom of the rectangle moves upward based on how long ago the note ended
        y_bottom = widget_height - (time_since_end * self.SCROLL_SPEED)
        
        # Keep the note visible as long as its BOTTOM edge (the last part to leave) 
        # hasn't completely scrolled above the widget (y_bottom >= 0)
        # Only remove when the bottom is completely above the top of the widget
        return y_bottom >= 0
    
    def set_scroll_speed(self, speed: float):
        """Set the scroll speed for the piano roll"""
        self.SCROLL_SPEED = max(10, min(500, speed))  # Clamp between 10 and 500 pixels per second
