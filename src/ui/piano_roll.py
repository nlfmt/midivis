from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QThread, QMutex, QMutexLocker
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QFont, QPainterPath, QRadialGradient
import time
import random
import math
from typing import Dict, List, Tuple


class Particle:
    """A single particle for visual effects"""
    def __init__(self, x: float, y: float, color: QColor, velocity_x: float, velocity_y: float, life: float, size: float, turbulence_strength: float = 1.0, damping_factor: float = 0.985):
        self.x = x
        self.y = y
        self.initial_color = color
        self.color = QColor(color)
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = life
        self.max_life = life
        self.size = size
        self.initial_size = self.size
        self.damping_factor = damping_factor
        
        # Enhanced turbulence parameters for much more visible swirly motion
        self.turbulence_time = random.uniform(0, math.pi * 2)  # Random phase offset
        self.turbulence_freq_x = random.uniform(1.2, 3.0)     # Much higher frequency for tighter swirls
        self.turbulence_freq_y = random.uniform(0.8, 2.5)     # Higher frequency for more visible swirls
        self.turbulence_amplitude = random.uniform(25, 45) * turbulence_strength    # Adjustable turbulence strength
        
        # Secondary noise layer for 2D Perlin-like effect with different scales
        self.noise_offset_x = random.uniform(0, 100)          # Random noise offset
        self.noise_offset_y = random.uniform(0, 100)
        self.turbulence_freq_x_2 = random.uniform(2.0, 4.5)  # Second layer with different frequency
        self.turbulence_freq_y_2 = random.uniform(1.5, 3.8)  # Second layer with different frequency
        self.turbulence_amplitude_2 = random.uniform(12, 25) * turbulence_strength # Secondary layer amplitude
        
    def reset(self, x: float, y: float, color: QColor, velocity_x: float, velocity_y: float, life: float, size: float, turbulence_strength: float = 1.0, damping_factor: float = 0.985):
        """Reset particle properties"""
        self.x = x
        self.y = y
        self.initial_color = color
        self.color = QColor(color)
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = life
        self.max_life = life
        self.size = size
        self.initial_size = size
        self.damping_factor = damping_factor
        
        # Reset turbulence parameters
        self.turbulence_time = random.uniform(0, math.pi * 2)
        self.turbulence_freq_x = random.uniform(1.2, 3.0)
        self.turbulence_freq_y = random.uniform(0.8, 2.5)
        self.turbulence_amplitude = random.uniform(25, 45) * turbulence_strength
        self.noise_offset_x = random.uniform(0, 100)
        self.noise_offset_y = random.uniform(0, 100)
        self.turbulence_freq_x_2 = random.uniform(2.0, 4.5)
        self.turbulence_freq_y_2 = random.uniform(1.5, 3.8)
        self.turbulence_amplitude_2 = random.uniform(12, 25) * turbulence_strength

    def update(self, dt: float):
        """Update particle position and fade"""
        # Update turbulence time - for swirly movement
        self.turbulence_time += dt * 2.0  # Faster time progression for more dynamic swirls

        # Simplified turbulence using sine waves
        time_x = self.turbulence_time + self.noise_offset_x
        time_y = self.turbulence_time + self.noise_offset_y

        turbulence_x = math.sin(time_x * self.turbulence_freq_x) * self.turbulence_amplitude * dt
        turbulence_y = math.cos(time_y * self.turbulence_freq_y) * self.turbulence_amplitude * dt

        # Apply base velocity with simplified turbulence
        self.x += (self.velocity_x * dt) + turbulence_x
        self.y += (self.velocity_y * dt) + turbulence_y

        self.life -= dt

        # Fade out as life decreases with steeper curve for better visibility
        alpha_ratio = max(0, self.life / self.max_life)
        alpha_curve = alpha_ratio * alpha_ratio  # Quadratic falloff for more dramatic fade
        self.color.setAlpha(int(255 * alpha_curve))

        # Shrink particle size over its lifespan
        base_size_ratio = max(0.1, self.life / self.max_life)
        self.size = self.initial_size * base_size_ratio

        # Apply configurable damping to slow down particles over time
        self.velocity_x *= self.damping_factor
        self.velocity_y *= self.damping_factor
    
    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0


class ParticlePool:
    """A pool to manage reusable particles."""
    def __init__(self, max_particles):
        self.max_particles = max_particles
        self.pool = []

    def get_particle(self):
        if self.pool:
            return self.pool.pop()
        return None

    def return_particle(self, particle):
        if len(self.pool) < self.max_particles:
            self.pool.append(particle)


class ParticleUpdateWorker(QThread):
    """Worker thread for updating particles."""
    def __init__(self, particles, mutex, parent=None):
        super().__init__(parent)
        self.particles = particles
        self.mutex = mutex
        self.running = True

    def run(self):
        while self.running:
            with QMutexLocker(self.mutex):
                current_time = time.time()
                dt = current_time - getattr(self, 'last_update_time', current_time)
                self.last_update_time = current_time

                # Update particles
                for particle in self.particles[:]:
                    particle.update(dt)
                    if not particle.is_alive():
                        self.particles.remove(particle)

            self.msleep(16)  # Approx. 60 FPS

    def stop(self):
        self.running = False
        self.wait()


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
        
        # Particle system
        self.particles: List[Particle] = []
        self.spark_particles: List[Particle] = []  # Small white spark particles
        self.last_particle_time = 0.0
        
        # Particle system configuration - centralized parameters for easy tweaking
        self.particle_config = {
            'spawn_rate': 0.01,                    # seconds between particle spawns per active note
            'initial_velocity_x_min': -5.0,       # minimum initial X velocity
            'initial_velocity_x_max': 5.0,        # maximum initial X velocity
            'initial_velocity_y_min': -80.0,      # minimum initial Y velocity (negative = upward)
            'initial_velocity_y_max': -30.0,       # maximum initial Y velocity (negative = upward)
            'initial_size_min': 0.4,              # minimum initial particle size
            'initial_size_max': 0.8,              # maximum initial particle size
            'initial_opacity_min': 40,            # minimum initial opacity (0-255)
            'initial_opacity_max': 80,            # maximum initial opacity (0-255)
            'turbulence_strength': 0.8,           # multiplier for turbulence amplitude (0.0-2.0+)
            'damping_factor': 0.995,              # velocity damping per frame (0.0-1.0, lower = more damping)
            'life_min': 0.5,                      # minimum particle life in seconds
            'life_max': 3.0,                      # maximum particle life in seconds
            'spawn_x_spread': 0.9,                # horizontal spread factor (0.0-1.0) across note width
            'particles_per_note_base': 2,         # base number of particles per note
            'particles_per_velocity': 20,         # velocity divisor for extra particles
            'max_particles_per_note': 15,                 # Maximum number of regular particles
            'max_particles': 500,                 # Maximum number of regular particles
            'max_spark_particles': 200,           # Maximum number of spark particles
            
            # Spark particle configuration
            'spark_enabled': True,                 # enable/disable spark particles
            'spark_size_min': 0.3,                # minimum spark particle size (increased for visibility)
            'spark_size_max': 0.5,                # maximum spark particle size (increased for visibility)
            'spark_opacity_min': 150,             # minimum spark opacity (0-255) (increased for visibility)
            'spark_opacity_max': 255,             # maximum spark opacity (0-255)
            'spark_life_min': 0.5,                # minimum spark life in seconds (increased for visibility)
            'spark_life_max': 2.0,                # maximum spark life in seconds (increased for visibility)
            'spark_count_ratio': 0.8,             # ratio of sparks to regular particles (increased for more sparks)
        }
        
        # Initialize particle pools for regular and spark particles
        self.particle_pool = ParticlePool(self.particle_config['max_particles'])
        self.spark_particle_pool = ParticlePool(self.particle_config['max_spark_particles'])
        
        # Pause functionality
        self.is_paused = False
        self.pause_start_time = 0.0  # When the pause started
        self.total_pause_duration = 0.0  # Total time spent paused
        
        # Colors for different velocities (brighter colors for better visibility) - DEPRECATED
        # Keeping for backward compatibility during transition
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
        
        # Static gradient configuration for note coloring
        # Notes will be colored based on their Y position, not velocity
        self.gradient_config = {
            'enabled': True,  # Enable gradient coloring
            'colors': [
                (255, 50, 50),    # Red (top of widget)
                (255, 150, 0),    # Orange (middle)
                (255, 100, 150),  # Pink (bottom of widget)
            ],
            'positions': [0.0, 0.5, 1.0],  # Relative positions (0=top, 1=bottom)
        }
        
        # Visual settings configuration
        self.visual_config = {
            'show_note_labels': False,  # Show note labels (C4, D4, etc.) inside notes
        }
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        # Track current time
        self.start_time = time.time()
        self.last_debug_time = 0
        self.last_update_time = time.time()  # For particle system timing
        
        self.setMinimumHeight(200)
        # Remove the stylesheet to avoid background conflicts
        # self.setStyleSheet("""
        #     background-color: #1a1a1a;
        #     border-radius: 8px;
        # """)
        
        self.cached_widget_width = 0
        self.cached_widget_height = 0
        
        # Thread-safe particle list and mutex
        self.particles_mutex = QMutex()

        # Particle update worker thread
        self.particle_worker = ParticleUpdateWorker(self.particles, self.particles_mutex)
        self.particle_worker.start()
    
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
        """Convert MIDI velocity to color - DEPRECATED, kept for compatibility"""
        # Map velocity (0-127) to color index
        color_index = min(9, velocity // 13)
        return self.velocity_colors[color_index]
    
    def position_to_gradient_color(self, y_position: float, widget_height: int) -> QColor:
        """Calculate color based on Y position using the static gradient
        
        Args:
            y_position: Y coordinate in the widget (0 = top, widget_height = bottom)
            widget_height: Height of the widget
            
        Returns:
            QColor based on the gradient configuration
        """
        if not self.gradient_config['enabled']:
            # Fallback to a default color if gradient is disabled
            return QColor(100, 170, 255)
        
        # Normalize position to 0.0 (top) to 1.0 (bottom)
        # Now the gradient colors are ordered from top to bottom
        normalized_pos = y_position / widget_height
        normalized_pos = max(0.0, min(1.0, normalized_pos))
        
        colors = self.gradient_config['colors']
        positions = self.gradient_config['positions']
        
        # Find the two colors to interpolate between
        if normalized_pos <= positions[0]:
            # Before first position, use first color
            r, g, b = colors[0]
            return QColor(r, g, b)
        elif normalized_pos >= positions[-1]:
            # After last position, use last color
            r, g, b = colors[-1]
            return QColor(r, g, b)
        else:
            # Find the segment to interpolate in
            for i in range(len(positions) - 1):
                if positions[i] <= normalized_pos <= positions[i + 1]:
                    # Calculate interpolation factor
                    segment_start = positions[i]
                    segment_end = positions[i + 1]
                    segment_length = segment_end - segment_start
                    factor = (normalized_pos - segment_start) / segment_length
                    
                    # Interpolate between the two colors
                    r1, g1, b1 = colors[i]
                    r2, g2, b2 = colors[i + 1]
                    
                    r = int(r1 + (r2 - r1) * factor)
                    g = int(g1 + (g2 - g1) * factor)
                    b = int(b1 + (b2 - b1) * factor)
                    
                    return QColor(r, g, b)
        
        # Fallback (shouldn't reach here)
        return QColor(100, 170, 255)
    
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
        self.particles.clear()  # Clear particles too
        self.spark_particles.clear()  # Clear spark particles too
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
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            widget_width = self.width()
            widget_height = self.height()
            
            # Cache widget scale to avoid redundant calculations
            if self.cached_widget_width != widget_width or self.cached_widget_height != widget_height:
                self.cached_widget_width = widget_width
                self.cached_widget_height = widget_height
                self.widget_scale = min(widget_width, widget_height) / 300.0
                self.widget_scale = max(0.5, min(3.0, self.widget_scale))
            
            # Update particles and timing
            current_real_time = time.time()
            dt = current_real_time - self.last_update_time
            self.last_update_time = current_real_time
            
            # Handle paused state for time calculation
            if self.is_paused:
                # While paused, use the time when we paused minus any previous pause durations
                current_time = self.pause_start_time - self.total_pause_duration
            else:
                # While playing, use current time minus all pause durations
                current_time = time.time() - self.total_pause_duration
            
            # Clear the entire widget with transparent background first
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            
            # Draw rounded background - much darker for better effect visibility
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(8, 8, 8)))
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
                    painter.setBrush(QBrush(QColor(8,8,8)))
                    painter.drawRect(QRectF(x, 0, key_width, widget_height))
            
            # Draw black keys (overlay)
            for i in range(self.NUM_KEYS):
                midi_note = i + self.LOWEST_NOTE
                x = self.key_index_to_x(i, widget_width)
                
                if self.is_black_key(midi_note):
                    # Draw black key - slightly darker than background
                    painter.setBrush(QBrush(QColor(6, 6, 6)))
                    painter.drawRect(QRectF(x, 0, key_width, widget_height))
            
            # Draw octave separators for C notes - much more subtle
            painter.setPen(QPen(QColor(20, 20, 20)))
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
            
            # Draw particles on top of everything
            self._draw_particles(painter)
            
            # Draw spark particles on top of regular particles
            self._draw_spark_particles(painter)
            
            # Spawn particles for active notes
            self._spawn_particles_for_active_notes(current_time, self.width(), self.height())
            
            # Update all particles
            self._update_particles(dt)
            
        except Exception as e:
            print(f"Error in paintEvent: {e}")
        finally:
            # Ensure painter is always properly ended
            painter.end()
    
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
        
        # Get color based on gradient position (use the middle of the note for color calculation)
        color_sample_y = (y_top + y_bottom) / 2
        base_color = self.position_to_gradient_color(color_sample_y, widget_height)
        
        # Make it brighter for active notes
        color = QColor(
            min(255, base_color.red() + 30),    # Reduced brightness boost (was +50)
            min(255, base_color.green() + 30),  # Same brightness as completed notes
            min(255, base_color.blue() + 30),
            220  # Slightly more opaque for active notes
        )
        
        # Create rect with slight inset for visibility
        rect_width = max(10, key_width * 0.9)
        x_center = x + (key_width / 2)
        rect = QRectF(x_center - (rect_width / 2), y_top, rect_width, rect_height)
        
        # Draw glow effect for active notes with stronger intensity
        self._draw_note_glow(painter, rect, color, intensity=1.5, widget_height=widget_height)
        
        # Draw a big bottom glow for active notes where they intersect with the bottom
        if y_bottom >= widget_height - 5:  # If note reaches near the bottom
            self._draw_bottom_glow(painter, rect, color, widget_height)
        
        # No border for active notes - remove the white outline
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Create a vertical gradient fill that shows the actual gradient across the note height
        gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        
        # Sample colors at multiple points along the note height
        num_samples = max(3, int(rect_height / 20))  # More samples for taller notes
        for i in range(num_samples):
            position = i / (num_samples - 1) if num_samples > 1 else 0
            sample_y = y_top + (y_bottom - y_top) * position
            sample_color = self.position_to_gradient_color(sample_y, widget_height)
            
            # Make it brighter for active notes
            enhanced_color = QColor(
                min(255, sample_color.red() + 50),
                min(255, sample_color.green() + 50),
                min(255, sample_color.blue() + 50),
                220
            )
            gradient.setColorAt(position, enhanced_color)
        
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners - more rounded for better appearance
        painter.drawRoundedRect(rect, 6, 6)
        
        # Draw note number inside if rectangle is big enough and labels are enabled
        if self.visual_config.get('show_note_labels', True) and rect_height > 14 and rect_width > 14:
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
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
        
        # Get color based on gradient position (use the middle of the note for color calculation)
        color_sample_y = (y_top_draw + y_bottom_draw) / 2
        base_color = self.position_to_gradient_color(color_sample_y, widget_height)
        
        # Normal brightness for completed notes
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
        
        # Draw subtle glow effect for completed notes with stronger intensity
        self._draw_note_glow(painter, rect, color, intensity=1.5, widget_height=widget_height)
        
        # No border for completed notes - just the solid color
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Create a vertical gradient fill that shows the actual gradient across the note height
        gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        
        # Sample colors at multiple points along the note height
        num_samples = max(3, int(rect_height / 20))  # More samples for taller notes
        for i in range(num_samples):
            position = i / (num_samples - 1) if num_samples > 1 else 0
            sample_y = y_top_draw + (y_bottom_draw - y_top_draw) * position
            sample_color = self.position_to_gradient_color(sample_y, widget_height)
            
            # Normal brightness for completed notes
            enhanced_color = QColor(
                min(255, sample_color.red() + 30),
                min(255, sample_color.green() + 30),
                min(255, sample_color.blue() + 30),
                240
            )
            gradient.setColorAt(position, enhanced_color)
        
        painter.setBrush(QBrush(gradient))
        
        # Draw with rounded corners for better appearance - more rounded
        painter.drawRoundedRect(rect, 6, 6)
        
        # Draw note number inside if rectangle is big enough and labels are enabled
        if self.visual_config.get('show_note_labels', True) and rect_height > 14 and rect_width > 14:
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
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
    
    def _update_particles(self, dt: float):
        """Update all particles"""
        try:
            # Update existing regular particles
            particles_to_keep = []
            for particle in self.particles:
                particle.update(dt)
                if particle.is_alive():
                    particles_to_keep.append(particle)
                else:
                    # Return particle to pool if not alive
                    self.particle_pool.return_particle(particle)
            self.particles = particles_to_keep
            
            # Update existing spark particles
            spark_particles_to_keep = []
            for particle in self.spark_particles:
                particle.update(dt)
                if particle.is_alive():
                    spark_particles_to_keep.append(particle)
                else:
                    # Return spark particle to pool if not alive
                    self.spark_particle_pool.return_particle(particle)
            self.spark_particles = spark_particles_to_keep
        except Exception as e:
            print(f"Error updating particles: {e}")
    
    def _spawn_particles_for_active_notes(self, current_time: float, widget_width: int, widget_height: int):
        """Spawn particles for active notes"""
        try:
            if current_time - self.last_particle_time < self.particle_config['spawn_rate']:
                return

            # Calculate widget scale factor for particle size and speed
            widget_scale = min(widget_width, widget_height) / 300.0  # Base scale on a 300px reference
            widget_scale = max(0.5, min(3.0, widget_scale))  # Clamp between 0.5x and 3x
            
            for note, (start_time, velocity) in self.active_notes.items():
                if start_time < current_time:
                    # Calculate particle spawn position - always on top of the note and at bottom of widget
                    key_index = self.note_to_key_index(note)
                    key_width = self.key_width(widget_width)
                    note_x_start = self.key_index_to_x(key_index, widget_width)
                    
                    # Get base color for particles from gradient (use bottom of widget for particles)
                    base_color = self.position_to_gradient_color(widget_height, widget_height)
                    
                    # Spawn multiple particles per note using configuration
                    base_particle_count = max(self.particle_config['particles_per_note_base'], 
                                            velocity // self.particle_config['particles_per_velocity'])
                    scaled_particle_count = int(base_particle_count * widget_scale)
                    num_particles = max(self.particle_config['particles_per_note_base'], 
                                      min(self.particle_config['max_particles_per_note'], scaled_particle_count))
                    
                    for _ in range(num_particles):
                        # Spawn particles at random X position across the note width, at bottom Y
                        px = note_x_start + random.uniform(0, key_width * self.particle_config['spawn_x_spread'])
                        py = widget_height  # Always spawn at bottom of widget
                        
                        # Use configurable initial velocities
                        vx = random.uniform(self.particle_config['initial_velocity_x_min'], 
                                          self.particle_config['initial_velocity_x_max']) * widget_scale
                        vy = random.uniform(self.particle_config['initial_velocity_y_min'], 
                                          self.particle_config['initial_velocity_y_max']) * widget_scale
                        
                        # Use configurable life span
                        life_variation = random.uniform(0.9, 1.2)
                        life = random.uniform(self.particle_config['life_min'], 
                                            self.particle_config['life_max']) * life_variation * (0.8 + 0.4 * widget_scale)
                        
                        # Create particle colors with configurable opacity
                        color_boost = random.randint(40, 100)  # More consistent color boost
                        opacity = random.randint(int(self.particle_config['initial_opacity_min']), 
                                               int(self.particle_config['initial_opacity_max']))
                        particle_color = QColor(
                            min(255, base_color.red() + color_boost),
                            min(255, base_color.green() + color_boost),
                            min(255, base_color.blue() + color_boost),
                            opacity
                        )
                        
                        # Use configurable particle sizes
                        size_variation = random.uniform(0.8, 1.2)
                        base_size = random.uniform(self.particle_config['initial_size_min'], 
                                                 self.particle_config['initial_size_max']) * size_variation
                        particle_size = base_size * widget_scale
                        particle_size = max(0.1, min(5.0, particle_size))  # Reasonable size limits
                        
                        # Create particle with configurable turbulence strength and damping
                        particle = self.particle_pool.get_particle()
                        if not particle:
                            particle = Particle(px, py, particle_color, vx, vy, life, particle_size, 
                                                self.particle_config['turbulence_strength'],
                                                self.particle_config['damping_factor'])
                        else:
                            particle.reset(px, py, particle_color, vx, vy, life, particle_size, 
                                           self.particle_config['turbulence_strength'],
                                           self.particle_config['damping_factor'])
                        self.particles.append(particle)
                    
                    # Spawn spark particles if enabled
                    if self.particle_config['spark_enabled']:
                        num_sparks = max(1, int(num_particles * self.particle_config['spark_count_ratio']))
                        
                        for _ in range(num_sparks):
                            # Spawn sparks at random X position across the note width, at bottom Y
                            spark_px = note_x_start + random.uniform(0, key_width * self.particle_config['spawn_x_spread'])
                            spark_py = widget_height  # Always spawn at bottom of widget
                            
                            # Use base particle velocity configuration but multiply by 1.5 for faster sparks
                            spark_vx = random.uniform(self.particle_config['initial_velocity_x_min'], 
                                                    self.particle_config['initial_velocity_x_max']) * widget_scale * 1.5
                            spark_vy = random.uniform(self.particle_config['initial_velocity_y_min'], 
                                                    self.particle_config['initial_velocity_y_max']) * widget_scale * 1.5
                            
                            # Use spark-specific life span
                            spark_life_variation = random.uniform(0.8, 1.2)
                            spark_life = random.uniform(self.particle_config['spark_life_min'], 
                                                       self.particle_config['spark_life_max']) * spark_life_variation
                            
                            # Create white spark particles with high opacity
                            spark_opacity = random.randint(int(self.particle_config['spark_opacity_min']), 
                                                         int(self.particle_config['spark_opacity_max']))
                            spark_color = QColor(255, 255, 255, spark_opacity)  # Pure white
                            
                            # Use spark-specific small sizes
                            spark_size_variation = random.uniform(0.8, 1.2)
                            spark_size = random.uniform(self.particle_config['spark_size_min'], 
                                                       self.particle_config['spark_size_max']) * spark_size_variation * widget_scale
                            spark_size = max(0.1, min(2.0, spark_size))  # Clamp spark size
                            
                            # Create spark particle with same movement parameters but different visuals
                            spark_particle = self.spark_particle_pool.get_particle()
                            if not spark_particle:
                                spark_particle = Particle(spark_px, spark_py, spark_color, spark_vx, spark_vy, spark_life, spark_size, 
                                                          self.particle_config['turbulence_strength'],
                                                          self.particle_config['damping_factor'])
                            else:
                                spark_particle.reset(spark_px, spark_py, spark_color, spark_vx, spark_vy, spark_life, spark_size, 
                                                     self.particle_config['turbulence_strength'],
                                                     self.particle_config['damping_factor'])
                            self.spark_particles.append(spark_particle)
            
            self.last_particle_time = current_time
        except Exception as e:
            print(f"Error spawning particles: {e}")
    
    def _draw_particles(self, painter: QPainter):
        """Draw all particles"""
        if not painter.isActive():
            return
            
        painter.setPen(Qt.PenStyle.NoPen)
        
        try:
            with QMutexLocker(self.particles_mutex):
                for particle in self.particles:
                    # Create radial gradient for particle glow effect - smaller glow radius
                    gradient = QRadialGradient(QPointF(particle.x, particle.y), particle.size * 1.2)
                    
                    # Center is bright and opaque
                    center_color = QColor(particle.color)
                    gradient.setColorAt(0, center_color)
                    
                    # Mid-point is slightly dimmer
                    mid_color = QColor(particle.color)
                    mid_color.setAlpha(int(particle.color.alpha() * 0.6))
                    gradient.setColorAt(0.6, mid_color)
                    
                    # Edge fades to transparent for glow effect
                    edge_color = QColor(particle.color)
                    edge_color.setAlpha(0)
                    gradient.setColorAt(1, edge_color)
                    
                    painter.setBrush(QBrush(gradient))
                    
                    # Draw particle as a glowing circle - size now changes over lifespan
                    particle_rect = QRectF(
                        particle.x - particle.size, 
                        particle.y - particle.size, 
                        particle.size * 2, 
                        particle.size * 2
                    )
                    painter.drawEllipse(particle_rect)
        except Exception as e:
            print(f"Error drawing particles: {e}")
    
    def _draw_spark_particles(self, painter: QPainter):
        """Draw spark particles with a more intense, star-like appearance"""
        if not painter.isActive():
            return
            
        painter.setPen(Qt.PenStyle.NoPen)
        
        try:
            for spark in self.spark_particles:
                # Create a bright white core with sharp falloff for spark effect
                gradient = QRadialGradient(QPointF(spark.x, spark.y), spark.size * 0.8)
                
                # Very bright white center
                center_color = QColor(spark.color)
                gradient.setColorAt(0, center_color)
                
                # Sharp falloff to create spark-like appearance
                mid_color = QColor(spark.color)
                mid_color.setAlpha(int(spark.color.alpha() * 0.3))
                gradient.setColorAt(0.4, mid_color)
                
                # Quick fade to transparent
                edge_color = QColor(spark.color)
                edge_color.setAlpha(0)
                gradient.setColorAt(1, edge_color)
                
                painter.setBrush(QBrush(gradient))
                
                # Draw spark as a small bright circle
                spark_rect = QRectF(
                    spark.x - spark.size, 
                    spark.y - spark.size, 
                    spark.size * 2, 
                    spark.size * 2
                )
                painter.drawEllipse(spark_rect)
                
                # Add a cross-shaped highlight for extra sparkle effect
                if spark.size > 0.3:  # Only for visible sparks
                    painter.setPen(QPen(QColor(255, 255, 255, int(spark.color.alpha() * 0.8)), max(0.5, spark.size * 0.3)))
                    
                    # Draw cross lines for sparkle effect
                    cross_size = spark.size * 1.5
                    painter.drawLine(QPointF(spark.x - cross_size, spark.y), QPointF(spark.x + cross_size, spark.y))
                    painter.drawLine(QPointF(spark.x, spark.y - cross_size), QPointF(spark.x, spark.y + cross_size))
                    
                    painter.setPen(Qt.PenStyle.NoPen)  # Reset pen
        except Exception as e:
            print(f"Error drawing spark particles: {e}")
    
    def _draw_note_glow(self, painter: QPainter, rect: QRectF, color: QColor, intensity: float = 1.0, widget_height: int = None):
        """Draw a glow effect around a note rectangle with gradient following the note"""
        # Save current state
        painter.save()
        
        # Create glow by drawing multiple layers with increasing size and decreasing opacity
        glow_layers = 3
        max_glow_size = 6 * intensity
        
        for i in range(glow_layers):
            layer_ratio = (i + 1) / glow_layers
            glow_size = max_glow_size * layer_ratio
            base_opacity = int((1.0 - layer_ratio) * 40)  # Reduced opacity for subtler glow
            
            # Expand rect for glow
            glow_rect = rect.adjusted(-glow_size, -glow_size, glow_size, glow_size)
            
            # Create gradient that follows the note's gradient if widget_height is provided
            if widget_height:
                gradient = QLinearGradient(glow_rect.left(), glow_rect.top(), glow_rect.left(), glow_rect.bottom())
                
                # Sample colors at multiple points along the glow height
                num_samples = 5
                for j in range(num_samples):
                    position = j / (num_samples - 1) if num_samples > 1 else 0
                    sample_y = glow_rect.top() + (glow_rect.bottom() - glow_rect.top()) * position
                    sample_color = self.position_to_gradient_color(sample_y, widget_height)
                    sample_color.setAlpha(base_opacity)
                    gradient.setColorAt(position, sample_color)
                
                painter.setBrush(QBrush(gradient))
            else:
                # Fallback to single color glow
                glow_color = QColor(color)
                glow_color.setAlpha(base_opacity)
                painter.setBrush(QBrush(glow_color))
            
            # Draw glow layer with more rounded corners
            painter.setPen(Qt.PenStyle.NoPen)
            corner_radius = 8 + glow_size  # More rounded corners that scale with glow size
            painter.drawRoundedRect(glow_rect, corner_radius, corner_radius)
        
        # Restore state
        painter.restore()
    
    def _draw_bottom_glow(self, painter: QPainter, rect: QRectF, color: QColor, widget_height: int):
        """Draw a big glow effect at the bottom of active notes with bottom gradient color"""
        # Save current state
        painter.save()
        
        # Create a radial gradient that emanates from the bottom center of the note
        bottom_center_x = rect.center().x()
        bottom_y = widget_height  # Bottom of the widget
        
        # Create a smaller but multi-layered glow for smoother falloff
        base_glow_radius = max(25, rect.width() * 1.0)  # Smaller base radius
        
        # Always use the bottom color from the gradient for this glow
        bottom_color = self.position_to_gradient_color(widget_height, widget_height)
        
        # Draw multiple glow layers for smooth falloff
        glow_layers = 3
        for layer in range(glow_layers):
            # Each layer gets progressively larger and more transparent
            layer_multiplier = 1.0 + (layer * 0.6)  # 1.0, 1.6, 2.2
            layer_radius = base_glow_radius * layer_multiplier
            
            # Create gradient for this layer
            gradient = QRadialGradient(bottom_center_x, bottom_y, layer_radius)
            
            # Base opacity decreases with each layer
            base_opacity = 100 - (layer * 25)  # 100, 75, 50
            
            # Create bright glow color for center using bottom gradient color
            glow_color = QColor(bottom_color)
            glow_color.setAlpha(base_opacity)
            gradient.setColorAt(0, glow_color)
            
            # Mid-point with reduced opacity
            mid_color = QColor(bottom_color)
            mid_color.setAlpha(int(base_opacity * 0.6))
            gradient.setColorAt(0.3, mid_color)
            
            # Another mid-point for smoother transition
            fade_color = QColor(bottom_color)
            fade_color.setAlpha(int(base_opacity * 0.3))
            gradient.setColorAt(0.6, fade_color)
            
            # Edge fades to transparent
            edge_color = QColor(bottom_color)
            edge_color.setAlpha(0)
            gradient.setColorAt(1, edge_color)
            
            # Draw this glow layer
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            
            glow_rect = QRectF(
                bottom_center_x - layer_radius,
                bottom_y - layer_radius,
                layer_radius * 2,
                layer_radius * 2
            )
            painter.drawEllipse(glow_rect)
        
        # Restore state
        painter.restore()
    
    def set_scroll_speed(self, speed: float):
        """Set the scroll speed for the piano roll"""
        self.SCROLL_SPEED = max(10, min(500, speed))  # Clamp between 10 and 500 pixels per second
    
    def update_particle_config(self, **kwargs):
        """Update particle configuration parameters
        
        Available parameters:
        - spawn_rate: seconds between particle spawns per active note
        - initial_velocity_x_min/max: X velocity range
        - initial_velocity_y_min/max: Y velocity range (negative = upward)
        - initial_size_min/max: particle size range
        - initial_opacity_min/max: opacity range (0-255)
        - turbulence_strength: turbulence multiplier (0.0-2.0+)
        - damping_factor: velocity damping per frame (0.0-1.0, lower = more damping)
        - life_min/max: particle lifespan range in seconds
        - spawn_x_spread: horizontal spread factor (0.0-1.0)
        - particles_per_note_base: base number of particles per note
        - particles_per_velocity: velocity divisor for extra particles
        - max_particles_per_note: maximum particles per note per spawn
        - spark_enabled: enable/disable spark particles
        - spark_size_min/max: spark particle size range
        - spark_opacity_min/max: spark opacity range (0-255)
        - spark_life_min/max: spark lifespan range in seconds
        - spark_count_ratio: ratio of sparks to regular particles
        """
        for key, value in kwargs.items():
            if key in self.particle_config:
                self.particle_config[key] = value
            else:
                print(f"Warning: Unknown particle config parameter: {key}")
                print(f"Available parameters: {list(self.particle_config.keys())}")
    
    def get_particle_config(self):
        """Get current particle configuration"""
        return self.particle_config.copy()
    
    def update_gradient_config(self, **kwargs):
        """Update gradient configuration parameters
        
        Available parameters:
        - enabled: bool - enable/disable gradient coloring
        - colors: list of (r, g, b) tuples - gradient colors
        - positions: list of floats - relative positions (0.0-1.0)
        """
        for key, value in kwargs.items():
            if key in self.gradient_config:
                self.gradient_config[key] = value
            else:
                print(f"Warning: Unknown gradient config parameter: {key}")
                print(f"Available parameters: {list(self.gradient_config.keys())}")
    
    def get_gradient_config(self):
        """Get current gradient configuration"""
        return self.gradient_config.copy()
    
    def set_gradient_colors(self, colors, positions=None):
        """Set gradient colors and optionally positions
        
        Args:
            colors: List of (r, g, b) tuples
            positions: Optional list of relative positions (0.0-1.0). If None, will be evenly distributed.
        """
        if not colors:
            return
        
        self.gradient_config['colors'] = colors
        
        if positions is None:
            # Evenly distribute positions
            if len(colors) == 1:
                positions = [0.5]
            else:
                positions = [i / (len(colors) - 1) for i in range(len(colors))]
        
        self.gradient_config['positions'] = positions
    
    def update_visual_config(self, **kwargs):
        """Update visual configuration parameters
        
        Available parameters:
        - show_note_labels: bool - show/hide note labels inside notes
        """
        for key, value in kwargs.items():
            if key in self.visual_config:
                self.visual_config[key] = value
            else:
                print(f"Warning: Unknown visual config parameter: {key}")
                print(f"Available parameters: {list(self.visual_config.keys())}")
    
    def get_visual_config(self):
        """Get current visual configuration"""
        return self.visual_config.copy()
    
    def closeEvent(self, event):
        """Ensure the worker thread is stopped when the widget is closed."""
        self.particle_worker.stop()
        super().closeEvent(event)

    def resizeEvent(self, event):
        """Handle widget resize - recompute gradient colors"""
        super().resizeEvent(event)
        
        widget_height = self.height()
        
        # Precompute gradient colors for a fixed number of positions
        self.precomputed_gradient_colors = []
        num_precomputed_positions = 100
        for i in range(num_precomputed_positions):
            normalized_pos = i / (num_precomputed_positions - 1)
            y_position = normalized_pos * widget_height
            color = self.position_to_gradient_color(y_position, widget_height)
            self.precomputed_gradient_colors.append(color)

    def position_to_precomputed_gradient_color(self, y_position: float, widget_height: int) -> QColor:
        """Get color from precomputed gradient colors based on Y position"""
        normalized_pos = y_position / widget_height
        index = int(normalized_pos * (len(self.precomputed_gradient_colors) - 1))
        return self.precomputed_gradient_colors[index]
