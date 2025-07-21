from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIcon, QFont

# Handle imports for both direct execution and package imports
try:
    from ..core.audio_manager import AudioManager, AudioDevice
    from ..core.settings_manager import SettingsManager
    # Defer spectrum analyzer import to reduce startup time
except ImportError:
    # For direct execution from src directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, current_dir)
    from core.audio_manager import AudioManager, AudioDevice
    from core.settings_manager import SettingsManager
    # Defer spectrum analyzer import to reduce startup time


class DeviceLoadWorker(QThread):
    """Worker thread for loading audio devices asynchronously"""
    
    devices_loaded = Signal(list, list)  # Emits lists of input and output AudioDevice objects
    error_occurred = Signal(str)         # Emits error message
    
    def __init__(self, audio_manager):
        super().__init__()
        self.audio_manager = audio_manager
    
    def run(self):
        """Load devices in background thread"""
        try:
            input_devices, output_devices = self.audio_manager.refresh_devices()
            self.devices_loaded.emit(input_devices, output_devices)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers (but don't load devices yet)
        self.audio_manager = AudioManager(lazy_init=True)  # Don't load devices in constructor
        self.settings_manager = SettingsManager()
        
        # UI components
        self.input_device_combo = None
        self.output_device_combo = None
        self.mute_button = None
        self.spectrum_analyzer = None
        self.device_worker = None
        
        # Loading state
        self.devices_loaded = False
        self.loading_device_settings = False  # Flag to prevent premature streaming during device loading
        self.input_device_map = {}  # Maps display names to device objects
        self.output_device_map = {}  # Maps display names to device objects
        
        # Setup window
        self.setWindowTitle("Audio Input Streamer")
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Start loading devices asynchronously
        self.start_device_loading()
    
    def start_device_loading(self):
        """Start loading audio devices in a background thread"""
        self.device_worker = DeviceLoadWorker(self.audio_manager)
        self.device_worker.devices_loaded.connect(self.on_devices_loaded)
        self.device_worker.error_occurred.connect(self.on_device_load_error)
        self.device_worker.start()
    
    def on_devices_loaded(self, input_devices, output_devices):
        """Handle devices loaded from background thread"""
        self.devices_loaded = True
        self.populate_device_combos(input_devices, output_devices)
        
        # Load settings now that devices are available
        self.load_device_settings()
        
        # Initialize spectrum analyzer now that we're ready
        self.initialize_spectrum_analyzer()
    
    def initialize_spectrum_analyzer(self):
        """Initialize the spectrum analyzer (deferred to reduce startup time)"""
        if self.spectrum_analyzer is None:
            try:
                # Import spectrum analyzer only when needed
                try:
                    from .spectrum_analyzer import SpectrumAnalyzer
                except ImportError:
                    from ui.spectrum_analyzer import SpectrumAnalyzer
                
                self.spectrum_analyzer = SpectrumAnalyzer()
                self.spectrum_analyzer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                
                # Replace placeholder with actual analyzer
                layout = self.centralWidget().layout()
                layout.replaceWidget(self.spectrum_placeholder, self.spectrum_analyzer)
                self.spectrum_placeholder.deleteLater()
                
                # Connect audio signal
                if hasattr(self.audio_manager, 'audio_data_ready'):
                    self.audio_manager.audio_data_ready.connect(self.spectrum_analyzer.add_audio_data)
                    
            except Exception as e:
                print(f"Failed to initialize spectrum analyzer: {e}")
                # Keep the placeholder if initialization fails
    
    def on_device_load_error(self, error_message):
        """Handle error loading devices"""
        self.input_device_combo.clear()
        self.input_device_combo.addItem(f"Error: {error_message}")
        self.input_device_combo.setEnabled(False)
        
        self.output_device_combo.clear()
        self.output_device_combo.addItem(f"Error: {error_message}")
        self.output_device_combo.setEnabled(False)
        
        self.show_error(f"Failed to load audio devices: {error_message}")
    
    def populate_device_combos(self, input_devices, output_devices):
        """Populate the device combo boxes with loaded devices"""
        # Clear mappings
        self.input_device_map.clear()
        self.output_device_map.clear()
        
        # Populate input devices
        self.input_device_combo.clear()
        self.input_device_combo.setPlaceholderText("Select input device...")
        self.input_device_combo.setEnabled(True)
        
        if not input_devices:
            self.input_device_combo.addItem("No input devices found")
            self.input_device_combo.setEnabled(False)
        else:
            for device in input_devices:
                display_name = f"{device.name} ({device.hostapi_name})"
                self.input_device_combo.addItem(display_name)
                self.input_device_map[display_name] = device
        
        # Populate output devices
        self.output_device_combo.clear()
        self.output_device_combo.setPlaceholderText("Select output device...")
        self.output_device_combo.setEnabled(True)
        
        # Add "Default Output" as first option
        self.output_device_combo.addItem("Default Output")
        self.output_device_map["Default Output"] = None  # None means use default
        
        if output_devices:
            for device in output_devices:
                # Show API type for better clarity
                api_short = {
                    'Windows WDM-KS': 'WDM-KS',
                    'Windows WASAPI': 'WASAPI', 
                    'Windows DirectSound': 'DirectSound'
                }.get(device.hostapi_name, device.hostapi_name)
                
                display_name = f"{device.name} ({api_short})"
                self.output_device_combo.addItem(display_name)
                self.output_device_map[display_name] = device
    
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
        
        # Device selection row - input and output side by side
        device_row = QHBoxLayout()
        device_row.setSpacing(8)
        
        self.input_device_combo = QComboBox()
        self.input_device_combo.setMinimumHeight(30)
        self.input_device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_device_combo.setPlaceholderText("Select input device...")
        self.input_device_combo.addItem("Loading input devices...")
        self.input_device_combo.setEnabled(False)  # Disabled until devices are loaded
        device_row.addWidget(self.input_device_combo, 1)
        
        self.output_device_combo = QComboBox()
        self.output_device_combo.setMinimumHeight(30)
        self.output_device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.output_device_combo.setPlaceholderText("Select output device...")
        self.output_device_combo.addItem("Loading output devices...")
        self.output_device_combo.setEnabled(False)  # Disabled until devices are loaded
        device_row.addWidget(self.output_device_combo, 1)
        
        # Combined status/mute button
        self.mute_button = QPushButton("Stopped")
        self.mute_button.setObjectName("status_mute_button")
        self.mute_button.setFixedSize(80, 30)
        self.mute_button.setProperty("muted", False)
        self.mute_button.setToolTip("Click to mute/unmute")
        device_row.addWidget(self.mute_button)
        
        layout.addLayout(device_row)
        
        # Placeholder for spectrum analyzer - will be replaced with actual analyzer when needed
        self.spectrum_placeholder = QLabel("Loading spectrum analyzer...")
        self.spectrum_placeholder.setMinimumHeight(120)
        self.spectrum_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.spectrum_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spectrum_placeholder.setStyleSheet("""
            background-color: #1e1e1e; 
            border: 1px solid #444;
            color: #888;
            font-size: 12px;
        """)
        layout.addWidget(self.spectrum_placeholder, 1)
        
        # Will be replaced later
        self.spectrum_analyzer = None
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Audio manager signals
        self.audio_manager.status_changed.connect(self.update_status)
        self.audio_manager.streaming_started.connect(self.on_streaming_started)
        self.audio_manager.streaming_stopped.connect(self.on_streaming_stopped)
        self.audio_manager.error_occurred.connect(self.show_error)
        # Note: audio_data_ready connection will be made when spectrum analyzer is initialized
        
        # UI signals
        self.input_device_combo.currentTextChanged.connect(self.on_input_device_changed)
        self.output_device_combo.currentTextChanged.connect(self.on_output_device_changed)
        self.mute_button.clicked.connect(self.toggle_mute)
    
    def on_input_device_changed(self, display_name: str):
        """Handle input device selection change"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error") or display_name == "No input devices found":
            return
        
        # Get device from mapping
        input_device = self.input_device_map.get(display_name)
        
        if input_device:
            # Save the device selection
            self.settings_manager.set_last_input_device(input_device.name)
            self.settings_manager.save_settings()
            
            # Only try to start streaming if we're not currently loading device settings
            if not self.loading_device_settings:
                self.try_start_streaming()
    
    def on_output_device_changed(self, display_name: str):
        """Handle output device selection change"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error"):
            return
        
        # Save the device selection
        self.settings_manager.set_last_output_device(display_name)
        self.settings_manager.save_settings()
        
        # Only try to start streaming if we're not currently loading device settings
        if not self.loading_device_settings:
            self.try_start_streaming()
    
    def try_start_streaming(self):
        """Try to start streaming only if both input and output devices are properly selected"""
        if not self.devices_loaded:
            return
        
        input_device = self.get_selected_input_device()
        output_device = self.get_selected_output_device()
        
        # Only start streaming if we have an input device
        # Output device can be None (default) but input device is required
        if input_device:
            self.audio_manager.start_streaming(input_device, output_device)
    
    def get_selected_input_device(self):
        """Get the currently selected input device"""
        display_name = self.input_device_combo.currentText()
        
        # Check if devices are loaded and we have a valid selection
        if (self.devices_loaded and 
            display_name and 
            not display_name.startswith("Loading") and 
            not display_name.startswith("Error") and
            display_name != "No input devices found" and
            display_name in self.input_device_map):
            
            return self.input_device_map.get(display_name)
        
        return None
    
    def get_selected_output_device(self):
        """Get the currently selected output device"""
        display_name = self.output_device_combo.currentText()
        
        # Check if devices are loaded and we have a valid selection
        if (self.devices_loaded and 
            display_name and 
            not display_name.startswith("Loading") and 
            not display_name.startswith("Error") and
            display_name in self.output_device_map):
            
            return self.output_device_map.get(display_name)
        
        return None
    
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
        # Clear spectrum when stopped (if analyzer is initialized)
        if self.spectrum_analyzer:
            self.spectrum_analyzer.clear_spectrum()
    
    def show_error(self, error_message: str):
        """Show error message"""
        QMessageBox.warning(self, "Audio Stream Error", error_message)
    
    def load_settings(self):
        """Load saved settings (except device which requires devices to be loaded first)"""
        # Load window geometry
        geometry = self.settings_manager.get_window_geometry()
        if geometry:
            try:
                self.restoreGeometry(geometry)
            except:
                pass  # Ignore geometry restore errors
    
    def load_device_settings(self):
        """Load device settings after devices are loaded"""
        # Set flag to prevent device change signals from starting streaming prematurely
        self.loading_device_settings = True
        
        # Load last input device
        last_input_device = self.settings_manager.get_last_input_device()
        if last_input_device:
            # Find the display name that corresponds to this device
            for display_name, device in self.input_device_map.items():
                if device and device.name == last_input_device:
                    index = self.input_device_combo.findText(display_name)
                    if index >= 0:
                        self.input_device_combo.setCurrentIndex(index)
                        break
        
        # Load last output device  
        last_output_device = self.settings_manager.get_last_output_device()
        if last_output_device:
            # Find exact match first
            index = self.output_device_combo.findText(last_output_device)
            if index >= 0:
                self.output_device_combo.setCurrentIndex(index)
            else:
                self.output_device_combo.setCurrentIndex(0)
        else:
            # Default to "Default Output" if no saved preference
            self.output_device_combo.setCurrentIndex(0)
        
        # Clear flag and try to start streaming now that both devices are loaded
        self.loading_device_settings = False
        self.try_start_streaming()

    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save current window geometry
        self.settings_manager.set_window_geometry(self.saveGeometry())
        self.settings_manager.save_settings()
        
        # Stop background worker if running
        if self.device_worker and self.device_worker.isRunning():
            self.device_worker.quit()
            self.device_worker.wait(1000)  # Wait up to 1 second
        
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
