"""
Real-time audio spectrum analyzer widget
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient
from scipy.fft import fft
from collections import deque


class SpectrumAnalyzer(QWidget):
    """Audio spectrum analyzer widget with real-time visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Spectrum parameters
        self.sample_rate = 44100
        self.fft_size = 4096  # Increased from 2048 for even better frequency resolution
        self.num_bars = 64
        self.frequency_range = (20, 20000)  # Hz
        
        # Visual parameters
        self.bar_width_ratio = 0.8  # Width of bars relative to available space
        self.peak_hold_time = 25  # Frames to hold peak values
        self.smoothing_factor = 0.08  # Much more responsive (reduced from 0.15)
        
        # Data storage
        self.audio_buffer = deque(maxlen=self.fft_size)
        self.spectrum_data = np.zeros(self.num_bars)
        self.peak_data = np.zeros(self.num_bars)
        self.peak_hold_counters = np.zeros(self.num_bars)
        
        # Calculate frequency bins
        self.setup_frequency_bins()
        
        # Setup colors and gradients
        self.setup_colors()
        
        # UI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(12)  # ~83 FPS for very smooth animation
        
        # Widget properties - allow it to grow to fill available space
        self.setMinimumHeight(120)
        # Remove maximum height constraint to allow unlimited growth
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), 
                          self.sizePolicy().Policy.Expanding)
        
    def setup_frequency_bins(self):
        """Setup frequency bins for logarithmic scale with better high-frequency coverage"""
        # Create logarithmic frequency scale
        log_min = np.log10(self.frequency_range[0])
        log_max = np.log10(self.frequency_range[1])
        log_frequencies = np.logspace(log_min, log_max, self.num_bars + 1)
        
        # Convert to FFT bin indices
        fft_freqs = np.fft.fftfreq(self.fft_size, 1.0 / self.sample_rate)[:self.fft_size // 2]
        max_freq = fft_freqs[-1]  # Nyquist frequency
        
        self.bin_indices = []
        for i in range(self.num_bars):
            # Find FFT bins that fall within this frequency band
            low_freq = log_frequencies[i]
            high_freq = min(log_frequencies[i + 1], max_freq)  # Don't exceed Nyquist
            
            low_bin = np.searchsorted(fft_freqs, low_freq)
            high_bin = np.searchsorted(fft_freqs, high_freq)
            
            # Ensure we have at least one bin
            if high_bin <= low_bin:
                high_bin = low_bin + 1
            
            # For the highest frequencies, ensure we capture up to Nyquist
            if i == self.num_bars - 1:
                high_bin = len(fft_freqs)
                
            self.bin_indices.append((low_bin, high_bin))
    
    def setup_colors(self):
        """Setup color gradients for the spectrum"""
        # Create gradient from blue to green to yellow to red
        self.gradient = QLinearGradient(0, 0, 0, 1)
        self.gradient.setColorAt(0.0, QColor(255, 50, 50))    # Red (top)
        self.gradient.setColorAt(0.3, QColor(255, 255, 50))  # Yellow
        self.gradient.setColorAt(0.6, QColor(50, 255, 50))   # Green
        self.gradient.setColorAt(1.0, QColor(50, 100, 255))  # Blue (bottom)
        
        # Peak line color
        self.peak_color = QColor(255, 255, 255, 200)
        
        # Background color
        self.bg_color = QColor(25, 25, 25)
    
    def add_audio_data(self, audio_data):
        """Add new audio data for spectrum analysis"""
        if len(audio_data.shape) > 1:
            # Convert stereo to mono by averaging channels
            audio_data = np.mean(audio_data, axis=1)
        
        # Add to buffer
        self.audio_buffer.extend(audio_data.flatten())
        
        # Process if we have enough data
        if len(self.audio_buffer) >= self.fft_size:
            self.process_spectrum()
    
    def process_spectrum(self):
        """Process audio buffer to generate spectrum data"""
        if len(self.audio_buffer) < self.fft_size:
            return
        
        # Get latest audio data
        audio_chunk = np.array(list(self.audio_buffer)[-self.fft_size:])
        
        # Apply window function to reduce spectral leakage
        window = np.hanning(self.fft_size)
        windowed_data = audio_chunk * window
        
        # Compute FFT
        fft_data = fft(windowed_data)
        magnitude = np.abs(fft_data[:self.fft_size // 2])
        
        # Proper FFT scaling for spectrum analysis
        # Scale by FFT size and window correction factor
        window_correction = np.sum(window) / self.fft_size
        magnitude = magnitude / (self.fft_size * window_correction)
        
        # Convert to dBFS (decibels relative to full scale)
        # Add small epsilon to avoid log(0)
        magnitude_db = 20 * np.log10(magnitude + 1e-12)
        
        # Group into frequency bands using energy-weighted approach
        new_spectrum = np.zeros(self.num_bars)
        for i, (low_bin, high_bin) in enumerate(self.bin_indices):
            if high_bin <= len(magnitude_db):
                band_data = magnitude_db[low_bin:high_bin]
                
                # Convert dB back to linear scale for proper energy weighting
                linear_magnitudes = 10 ** (band_data / 20)
                
                # Use RMS (Root Mean Square) which better represents energy
                # This gives more weight to stronger frequencies in the band
                rms_magnitude = np.sqrt(np.mean(linear_magnitudes ** 2))
                
                # Convert back to dB
                band_magnitude = 20 * np.log10(rms_magnitude + 1e-12)
                
                # Apply slight high-frequency compensation for better visibility
                freq_center = np.sqrt(self.get_frequency_for_bin(low_bin) * self.get_frequency_for_bin(high_bin))
                if freq_center > 2000:  # Subtle boost for high frequencies only
                    compensation = min(6.0, np.log10(freq_center / 2000) * 3.0)
                    band_magnitude += compensation
                
                # Normalize to 0-1 range using -80dB to -20dB range for better use of visual space
                normalized = (band_magnitude + 80) / 60
                new_spectrum[i] = max(0, min(1, normalized))
        
        # Less smoothing for more responsive display
        self.spectrum_data = (self.smoothing_factor * new_spectrum + 
                             (1 - self.smoothing_factor) * self.spectrum_data)
        
        # Update peak hold
        for i in range(self.num_bars):
            if self.spectrum_data[i] > self.peak_data[i]:
                self.peak_data[i] = self.spectrum_data[i]
                self.peak_hold_counters[i] = self.peak_hold_time
            elif self.peak_hold_counters[i] > 0:
                self.peak_hold_counters[i] -= 1
            else:
                self.peak_data[i] *= 0.92  # Faster decay for more responsive peaks
    
    def get_frequency_for_bin(self, bin_index):
        """Get the frequency for a given FFT bin index"""
        return bin_index * self.sample_rate / self.fft_size
    
    def paintEvent(self, event):
        """Paint the spectrum analyzer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw rounded background frame
        frame_rect = self.rect().adjusted(1, 1, -1, -1)  # Small margin for border
        painter.setPen(QPen(QColor(51, 51, 51), 1))  # Border color
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRoundedRect(frame_rect, 8, 8)  # Rounded corners
        
        if self.num_bars == 0:
            return
        
        # Calculate bar dimensions with margin for rounded frame
        margin = 8
        width = self.width() - (margin * 2)
        height = self.height() - (margin * 2)
        bar_width = (width / self.num_bars) * self.bar_width_ratio
        bar_spacing = width / self.num_bars
        
        # Set up gradient for bars
        gradient = QLinearGradient(0, height + margin, 0, margin)
        gradient.setColorAt(0.0, QColor(50, 100, 255))   # Blue (bottom)
        gradient.setColorAt(0.6, QColor(50, 255, 50))    # Green
        gradient.setColorAt(0.8, QColor(255, 255, 50))   # Yellow
        gradient.setColorAt(1.0, QColor(255, 50, 50))    # Red (top)
        
        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Set clipping region to rounded rect to ensure bars don't extend outside
        painter.setClipRect(frame_rect)
        
        # Draw spectrum bars
        for i in range(self.num_bars):
            x = margin + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = self.spectrum_data[i] * height
            y = margin + height - bar_height
            
            # Draw main bar
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)
            
            # Draw peak line
            if self.peak_data[i] > 0.01:  # Only draw if peak is significant
                peak_y = margin + height - (self.peak_data[i] * height)
                painter.setPen(QPen(self.peak_color, 1))
                painter.drawLine(x, peak_y, x + bar_width, peak_y)
                painter.setPen(Qt.PenStyle.NoPen)
    
    def clear_spectrum(self):
        """Clear the spectrum data"""
        self.spectrum_data.fill(0)
        self.peak_data.fill(0)
        self.peak_hold_counters.fill(0)
        self.audio_buffer.clear()
        self.update()
