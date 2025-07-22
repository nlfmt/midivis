from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIcon, QFont

# Handle imports for both direct execution and package imports
try:
    from ..core.audio_manager import AudioManager, AudioDevice
    from ..core.settings_manager import SettingsManager
    from ..core.midi_manager import MIDIManager, MIDIDevice
    # Defer spectrum analyzer import to reduce startup time
except ImportError:
    # For direct execution from src directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, current_dir)
    from core.audio_manager import AudioManager, AudioDevice
    from core.settings_manager import SettingsManager
    from core.midi_manager import MIDIManager, MIDIDevice
    # Defer spectrum analyzer import to reduce startup time


class DeviceLoadWorker(QThread):
    """Worker thread for loading audio and MIDI devices asynchronously"""
    
    devices_loaded = Signal(list, list, list)  # Emits lists of input, output AudioDevice objects, and MIDI devices
    error_occurred = Signal(str)         # Emits error message
    
    def __init__(self, audio_manager, midi_manager):
        super().__init__()
        self.audio_manager = audio_manager
        self.midi_manager = midi_manager
    
    def run(self):
        """Load devices in background thread"""
        try:
            input_devices, output_devices = self.audio_manager.refresh_devices()
            midi_devices = self.midi_manager.refresh_devices()
            self.devices_loaded.emit(input_devices, output_devices, midi_devices)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers (but don't load devices yet)
        self.audio_manager = AudioManager(lazy_init=True)  # Don't load devices in constructor
        self.midi_manager = MIDIManager()
        self.settings_manager = SettingsManager()
        
        # UI components
        self.input_device_combo = None
        self.output_device_combo = None
        self.midi_device_combo = None
        self.mute_button = None
        self.view_toggle_button = None
        self.spectrum_analyzer = None
        self.piano_roll = None
        self.device_worker = None
        
        # Loading state
        self.devices_loaded = False
        self.loading_device_settings = False  # Flag to prevent premature streaming during device loading
        self.input_device_map = {}  # Maps display names to device objects
        self.output_device_map = {}  # Maps display names to device objects
        self.midi_device_map = {}   # Maps display names to MIDI device objects
        self.show_piano_roll = False  # Toggle between spectrum and piano roll
        
        # Setup window
        self.setWindowTitle("Audio Input Streamer")
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Start loading devices asynchronously
        self.start_device_loading()
    
    def start_device_loading(self):
        """Start loading audio and MIDI devices in a background thread"""
        self.device_worker = DeviceLoadWorker(self.audio_manager, self.midi_manager)
        self.device_worker.devices_loaded.connect(self.on_devices_loaded)
        self.device_worker.error_occurred.connect(self.on_device_load_error)
        self.device_worker.start()
    
    def on_devices_loaded(self, input_devices, output_devices, midi_devices):
        """Handle devices loaded from background thread"""
        self.devices_loaded = True
        self.populate_device_combos(input_devices, output_devices, midi_devices)
        
        # Load settings now that devices are available
        self.load_device_settings()
        
        # Initialize spectrum analyzer and piano roll now that we're ready
        self.initialize_visualization_widgets()
    
    def initialize_visualization_widgets(self):
        """Initialize the spectrum analyzer and piano roll (deferred to reduce startup time)"""
        central_widget = self.centralWidget()
        
        if self.spectrum_analyzer is None:
            try:
                # Import spectrum analyzer only when needed
                try:
                    from .spectrum_analyzer import SpectrumAnalyzer
                except ImportError:
                    from ui.spectrum_analyzer import SpectrumAnalyzer
                
                self.spectrum_analyzer = SpectrumAnalyzer(parent=central_widget)
                self.spectrum_analyzer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                self.spectrum_analyzer.setMinimumHeight(200)
                
                # Connect audio signal
                if hasattr(self.audio_manager, 'audio_data_ready'):
                    self.audio_manager.audio_data_ready.connect(self.spectrum_analyzer.add_audio_data)
                    
            except Exception as e:
                print(f"Failed to initialize spectrum analyzer: {e}")
                
        if self.piano_roll is None:
            try:
                # Import piano roll only when needed
                try:
                    from .piano_roll import PianoRollWidget
                except ImportError:
                    from ui.piano_roll import PianoRollWidget
                
                self.piano_roll = PianoRollWidget(parent=central_widget)
                self.piano_roll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                self.piano_roll.setMinimumHeight(200)
                
                # Connect MIDI signals
                self.midi_manager.note_on.connect(self.piano_roll.add_note_on)
                self.midi_manager.note_off.connect(self.piano_roll.add_note_off)
                
            except Exception as e:
                print(f"Failed to initialize piano roll: {e}")
        
        # Update visualization widget based on current setting
        self.update_visualization_widget()
        
        # Add test functionality - double-click piano roll button to test
        self.view_toggle_button.mouseDoubleClickEvent = self.test_piano_roll_display
    
    def on_device_load_error(self, error_message):
        """Handle error loading devices"""
        self.input_device_combo.clear()
        self.input_device_combo.addItem(f"Error: {error_message}")
        self.input_device_combo.setEnabled(False)
        
        self.output_device_combo.clear()
        self.output_device_combo.addItem(f"Error: {error_message}")
        self.output_device_combo.setEnabled(False)
        
        self.midi_device_combo.clear()
        self.midi_device_combo.addItem(f"Error: {error_message}")
        self.midi_device_combo.setEnabled(False)
        
        self.show_error(f"Failed to load devices: {error_message}")
    
    def populate_device_combos(self, input_devices, output_devices, midi_devices):
        """Populate the device combo boxes with loaded devices"""
        # Clear mappings
        self.input_device_map.clear()
        self.output_device_map.clear()
        self.midi_device_map.clear()
        
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
        
        # Populate MIDI devices
        self.midi_device_combo.clear()
        self.midi_device_combo.setPlaceholderText("Select MIDI device...")
        self.midi_device_combo.setEnabled(True)
        
        # Add "No MIDI" as first option
        self.midi_device_combo.addItem("No MIDI")
        self.midi_device_map["No MIDI"] = None
        
        if not midi_devices:
            self.midi_device_combo.addItem("No MIDI devices found")
        else:
            for device in midi_devices:
                display_name = device.name
                self.midi_device_combo.addItem(display_name)
                self.midi_device_map[display_name] = device
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setMinimumSize(350, 280)  # Minimum size for usability (increased for MIDI row)
        self.resize(450, 430)  # Default size (increased for MIDI row)
        
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
        
        # MIDI and visualization control row
        midi_row = QHBoxLayout()
        midi_row.setSpacing(8)
        
        self.midi_device_combo = QComboBox()
        self.midi_device_combo.setMinimumHeight(30)
        self.midi_device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.midi_device_combo.setPlaceholderText("Select MIDI device...")
        self.midi_device_combo.addItem("Loading MIDI devices...")
        self.midi_device_combo.setEnabled(False)  # Disabled until devices are loaded
        midi_row.addWidget(self.midi_device_combo, 1)
        
        # View toggle button
        self.view_toggle_button = QPushButton("Piano Roll")
        self.view_toggle_button.setFixedSize(80, 30)
        self.view_toggle_button.setToolTip("Switch between spectrum analyzer and piano roll")
        midi_row.addWidget(self.view_toggle_button)
        
        layout.addLayout(midi_row)
        
        # Placeholder for visualization widgets - will be replaced with actual widgets when needed
        self.spectrum_placeholder = QLabel("Loading visualization...")
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
        self.piano_roll = None
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Audio manager signals
        self.audio_manager.status_changed.connect(self.update_status)
        self.audio_manager.streaming_started.connect(self.on_streaming_started)
        self.audio_manager.streaming_stopped.connect(self.on_streaming_stopped)
        self.audio_manager.error_occurred.connect(self.show_error)
        # Note: audio_data_ready connection will be made when spectrum analyzer is initialized
        
        # MIDI manager signals
        self.midi_manager.error_occurred.connect(self.show_error)
        
        # UI signals
        self.input_device_combo.currentTextChanged.connect(self.on_input_device_changed)
        self.output_device_combo.currentTextChanged.connect(self.on_output_device_changed)
        self.midi_device_combo.currentTextChanged.connect(self.on_midi_device_changed)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.view_toggle_button.clicked.connect(self.toggle_visualization)
    
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
    
    def on_midi_device_changed(self, display_name: str):
        """Handle MIDI device selection change"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error"):
            return
        
        # Get device from mapping
        midi_device = self.midi_device_map.get(display_name)
        
        if midi_device:
            # Test device first
            if self.midi_manager.test_device(midi_device):
                # Start MIDI listening
                success = self.midi_manager.start_listening(midi_device)
                if success:
                    # Save the device selection
                    self.settings_manager.set_last_midi_device(midi_device.name)
                    self.settings_manager.save_settings()
                    print(f"MIDI device '{midi_device.name}' connected successfully")
                else:
                    print(f"Failed to start listening on MIDI device '{midi_device.name}'")
            else:
                print(f"MIDI device '{midi_device.name}' test failed - device may be in use")
                self.show_error(f"Cannot use MIDI device '{midi_device.name}' - it may be in use by another application")
        else:
            # "No MIDI" selected - stop MIDI listening
            self.midi_manager.stop_listening()
            if display_name == "No MIDI":
                self.settings_manager.set_last_midi_device("")
                self.settings_manager.save_settings()
    
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
        
        # Load last MIDI device
        last_midi_device = self.settings_manager.get_last_midi_device()
        if last_midi_device:
            # Find the display name that corresponds to this device
            for display_name, device in self.midi_device_map.items():
                if device and device.name == last_midi_device:
                    index = self.midi_device_combo.findText(display_name)
                    if index >= 0:
                        self.midi_device_combo.setCurrentIndex(index)
                        break
        else:
            # Default to "No MIDI" if no saved preference
            self.midi_device_combo.setCurrentIndex(0)
        
        # Load view preference
        self.show_piano_roll = self.settings_manager.get_show_piano_roll()
        
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
        
        # Stop audio streaming and MIDI listening
        self.audio_manager.stop_streaming()
        self.midi_manager.stop_listening()
        
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
    
    def update_visualization_widget(self):
        """Update which visualization widget is shown"""
        layout = self.centralWidget().layout()
        
        # Get the current visualization widget or placeholder
        current_widget = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() in [self.spectrum_placeholder, self.spectrum_analyzer, self.piano_roll]:
                current_widget = item.widget()
                break
                
        if not current_widget:
            return
            
        # Handle switch to piano roll
        if self.show_piano_roll:
            if not self.piano_roll:
                return
                
            if current_widget != self.piano_roll:
                # Replace current widget with piano roll
                layout.removeWidget(current_widget)
                current_widget.hide()
                current_widget.setParent(None)
                
                # Add piano roll
                layout.addWidget(self.piano_roll, 1)
                self.piano_roll.show()
                self.piano_roll.raise_()
                
                # Update button text
                self.view_toggle_button.setText("Spectrum")
        
        # Handle switch to spectrum analyzer
        else:
            if not self.spectrum_analyzer:
                return
                
            if current_widget != self.spectrum_analyzer:
                # Replace current widget with spectrum analyzer
                layout.removeWidget(current_widget)
                current_widget.hide()
                current_widget.setParent(None)
                
                # Add spectrum analyzer
                layout.addWidget(self.spectrum_analyzer, 1)
                self.spectrum_analyzer.show()
                self.spectrum_analyzer.raise_()
                
                # Update button text
                self.view_toggle_button.setText("Piano Roll")
    
    def toggle_visualization(self):
        """Toggle between spectrum analyzer and piano roll"""
        self.show_piano_roll = not self.show_piano_roll
        self.update_visualization_widget()
        
        # Save preference
        self.settings_manager.set_show_piano_roll(self.show_piano_roll)
        self.settings_manager.save_settings()
    
    def test_piano_roll_display(self, event=None):
        """Test method to toggle to piano roll and add sample notes"""
        # Force switch to piano roll
        self.show_piano_roll = True
        self.update_visualization_widget()
        
        # Add test notes if piano roll is available
        if self.piano_roll:
            self.piano_roll.test_piano_roll()
