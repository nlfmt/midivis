from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont
from audio_manager import AudioManager, AudioDevice
from settings_manager import SettingsManager


class StatusIndicator(QFrame):
    """Custom status indicator widget"""
    def __init__(self):
        super().__init__()
        self.setObjectName("status_indicator")
        self.setFixedSize(16, 16)
        self.set_status("stopped")
    
    def set_status(self, status: str):
        """Set the status (streaming, error, stopped)"""
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)


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
        self.refresh_button = None
        self.status_label = None
        self.status_indicator = None
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Auto-start streaming after a short delay
        QTimer.singleShot(100, self.auto_start_streaming)
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Audio Input Streamer")
        self.setMinimumSize(500, 350)
        self.resize(550, 400)
        # Remove maximum size constraint to allow proper resizing
        self.setMaximumSize(16777215, 16777215)  # Qt's QWIDGETSIZE_MAX
        
        # Main widget and layout
        main_widget = QWidget()
        main_widget.setObjectName("main_frame")
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Audio Input Streamer")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Device selection section
        device_frame = QFrame()
        device_layout = QVBoxLayout(device_frame)
        device_layout.setSpacing(15)
        device_layout.setContentsMargins(20, 20, 20, 20)
        
        device_label = QLabel("Select Input Device:")
        device_layout.addWidget(device_label)
        
        # Device combo and refresh button row
        device_row = QHBoxLayout()
        device_row.setSpacing(15)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(50)
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.refresh_devices()
        device_row.addWidget(self.device_combo, 1)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setObjectName("refresh_button")
        self.refresh_button.setFixedSize(50, 50)
        self.refresh_button.setToolTip("Refresh device list")
        device_row.addWidget(self.refresh_button)
        
        device_layout.addLayout(device_row)
        layout.addWidget(device_frame)
        
        # Controls section
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(20)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        
        self.mute_button = QPushButton("🔊 Unmuted")
        self.mute_button.setObjectName("mute_button")
        self.mute_button.setMinimumHeight(55)
        self.mute_button.setMinimumWidth(200)
        self.mute_button.setProperty("muted", False)
        controls_layout.addWidget(self.mute_button)
        
        layout.addWidget(controls_frame)
        
        # Status section
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 15, 20, 15)
        status_layout.setSpacing(15)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("status_label")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        status_layout.addWidget(self.status_label, 1)
        
        self.status_indicator = StatusIndicator()
        status_layout.addWidget(self.status_indicator)
        
        layout.addWidget(status_frame)
        
        # Add some stretch at the bottom
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Audio manager signals
        self.audio_manager.status_changed.connect(self.update_status)
        self.audio_manager.streaming_started.connect(self.on_streaming_started)
        self.audio_manager.streaming_stopped.connect(self.on_streaming_stopped)
        self.audio_manager.error_occurred.connect(self.show_error)
        
        # UI signals
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.refresh_button.clicked.connect(self.refresh_devices)
    
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
            self.mute_button.setText("🔇 Muted")
            self.mute_button.setProperty("muted", True)
        else:
            self.mute_button.setText("🔊 Unmuted")
            self.mute_button.setProperty("muted", False)
        
        # Refresh button style
        self.mute_button.style().unpolish(self.mute_button)
        self.mute_button.style().polish(self.mute_button)
    
    def update_status(self, message: str, color: str):
        """Update status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
        
        # Update status indicator
        if "error" in message.lower() or "failed" in message.lower():
            self.status_indicator.set_status("error")
        elif "streaming" in message.lower():
            self.status_indicator.set_status("streaming")
        else:
            self.status_indicator.set_status("stopped")
    
    def on_streaming_started(self, device_name: str):
        """Handle streaming started"""
        self.status_indicator.set_status("streaming")
    
    def on_streaming_stopped(self):
        """Handle streaming stopped"""
        self.status_indicator.set_status("stopped")
    
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
