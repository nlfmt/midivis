from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

# Handle imports for both direct execution and package imports
try:
    from ..core.audio_manager import AudioManager, AudioDevice
    from ..core.settings_manager import SettingsManager
    from .spectrum_analyzer import SpectrumAnalyzer
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    from core.audio_manager import AudioManager, AudioDevice
    from core.settings_manager import SettingsManager
    sys.path.insert(0, current_dir)
    from spectrum_analyzer import SpectrumAnalyzer


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.audio_manager = AudioManager()
        self.settings_manager = SettingsManager()
        
        # UI components
        self.device_combo = None
        self.mute_button = None
        self.spectrum_analyzer = None
        
        # Setup window
        self.setWindowTitle("Audio Input Streamer")
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Auto-start streaming after a short delay
        QTimer.singleShot(100, self.auto_start_streaming)
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setMinimumSize(350, 240)  # Minimum size for usability
        self.resize(450, 390)  # Default size
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Device selection row
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(30)
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.device_combo.setPlaceholderText("Select device...")
        self.refresh_devices()
        device_row.addWidget(self.device_combo, 1)
        
        # Combined status/mute button
        self.mute_button = QPushButton("Stopped")
        self.mute_button.setObjectName("status_mute_button")
        self.mute_button.setFixedSize(80, 30)
        self.mute_button.setProperty("muted", False)
        self.mute_button.setToolTip("Click to mute/unmute")
        device_row.addWidget(self.mute_button)
        
        layout.addLayout(device_row)
        
        # Spectrum analyzer - takes up the rest of the window
        self.spectrum_analyzer = SpectrumAnalyzer()
        self.spectrum_analyzer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.spectrum_analyzer, 1)
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Audio manager signals
        self.audio_manager.status_changed.connect(self.update_status)
        self.audio_manager.streaming_started.connect(self.on_streaming_started)
        self.audio_manager.streaming_stopped.connect(self.on_streaming_stopped)
        self.audio_manager.error_occurred.connect(self.show_error)
        self.audio_manager.audio_data_ready.connect(self.spectrum_analyzer.add_audio_data)
        
        # UI signals
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        self.mute_button.clicked.connect(self.toggle_mute)
    
    def refresh_devices(self):
        """Refresh the device list"""
        current_device = self.device_combo.currentText() if self.device_combo.count() > 0 else ""
        
        self.device_combo.clear()
        devices = self.audio_manager.refresh_devices()
        
        if not devices:
            self.device_combo.addItem("No input devices found")
            self.device_combo.setEnabled(False)
            return
        
        self.device_combo.setEnabled(True)
        for device in devices:
            self.device_combo.addItem(device.name)
        
        # Try to restore previous selection
        if current_device:
            index = self.device_combo.findText(current_device)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
    
    def on_device_changed(self, device_name: str):
        """Handle device selection change"""
        if not device_name or device_name == "No input devices found":
            return
        
        device = self.audio_manager.get_device_by_name(device_name)
        if device:
            self.audio_manager.start_streaming(device)
            self.settings_manager.set_last_device(device_name)
            self.settings_manager.save_settings()
    
    def toggle_mute(self):
        """Toggle mute state"""
        is_muted = self.audio_manager.toggle_mute()
        
        if is_muted:
            self.mute_button.setText("Muted")
            self.mute_button.setProperty("muted", True)
            self.mute_button.setToolTip("Click to unmute")
        else:
            self.mute_button.setText("Streaming")
            self.mute_button.setProperty("muted", False)
            self.mute_button.setToolTip("Click to mute")
        
        # Refresh button style
        self.mute_button.style().unpolish(self.mute_button)
        self.mute_button.style().polish(self.mute_button)
    
    def update_status(self, message: str, color: str):
        """Update status in the window title"""
        self.setWindowTitle(f"Audio Input Streamer - {message}")
    
    def on_streaming_started(self, device_name: str):
        """Handle streaming started"""
        if not self.audio_manager.is_muted:
            self.mute_button.setText("Streaming")
            self.mute_button.setProperty("muted", False)
            self.mute_button.style().unpolish(self.mute_button)
            self.mute_button.style().polish(self.mute_button)
    
    def on_streaming_stopped(self):
        """Handle streaming stopped"""
        self.mute_button.setText("Stopped")
        self.mute_button.setProperty("muted", False)
        self.mute_button.style().unpolish(self.mute_button)
        self.mute_button.style().polish(self.mute_button)
        # Clear spectrum when stopped
        self.spectrum_analyzer.clear_spectrum()
    
    def show_error(self, error_message: str):
        """Show error message"""
        QMessageBox.warning(self, "Audio Stream Error", error_message)
    
    def load_settings(self):
        """Load saved settings"""
        # Load last device
        last_device = self.settings_manager.get_last_device()
        if last_device:
            index = self.device_combo.findText(last_device)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
            else:
                self.update_status("Saved device not found", "#ff8800")
        
        # Load window geometry
        geometry = self.settings_manager.get_window_geometry()
        if geometry:
            try:
                self.restoreGeometry(geometry)
            except:
                pass  # Ignore geometry restore errors
    
    def auto_start_streaming(self):
        """Auto-start streaming with selected device"""
        if self.device_combo.count() > 0 and self.device_combo.isEnabled():
            current_text = self.device_combo.currentText()
            if current_text and current_text != "No input devices found":
                self.on_device_changed(current_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save current window geometry
        self.settings_manager.set_window_geometry(self.saveGeometry())
        self.settings_manager.save_settings()
        
        # Stop audio streaming
        self.audio_manager.stop_streaming()
        
        event.accept()
    
    def showEvent(self, event):
        """Handle window show event - apply dark title bar on Windows"""
        super().showEvent(event)
        
        # Apply dark title bar if the function is available
        app = QApplication.instance()
        if hasattr(app, 'enable_dark_title_bar'):
            try:
                # Get the window handle
                hwnd = int(self.winId())
                app.enable_dark_title_bar(hwnd)
            except Exception:
                pass  # Silently fail if not supported
