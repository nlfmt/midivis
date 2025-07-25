from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy, QApplication, QSpinBox)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QKeySequence, QShortcut

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
        
        # Current device selections (the source of truth)
        self.current_input_device = None    # AudioDevice object
        self.current_output_device = None   # AudioDevice object or "Default Output"
        self.current_midi_device = None     # MIDIDevice object or None
        
        # UI components
        self.toolbar = None
        self.scroll_speed_input = None
        self.midi_delay_input = None
        self.play_pause_button = None
        self.clear_button = None
        self.particles_button = None
        self.devices_button = None  # New devices button
        self.mute_button = None
        self.view_toggle_button = None
        self.spectrum_analyzer = None
        self.piano_roll = None
        self.device_worker = None
        self.device_config_dialog = None  # Device configuration dialog
        self.demo_shortcut = None  # F8 keyboard shortcut for demo mode
        self.reload_shortcut = None
        self.fullscreen_shortcut = None  # F11 keyboard shortcut for fullscreen
        self.toolbar_shortcut = None  # F9 keyboard shortcut for toolbar toggle
        
        # Loading state
        self.devices_loaded = False
        self.input_device_map = {}  # Maps display names to device objects
        self.output_device_map = {}  # Maps display names to device objects
        self.midi_device_map = {}   # Maps display names to MIDI device objects
        self.show_piano_roll = True  # Toggle between spectrum and piano roll
        
        # Setup window
        self.setWindowTitle("Midivis")
        
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
        self.populate_device_maps(input_devices, output_devices, midi_devices)
        
        # Update device config dialog if it exists
        if self.device_config_dialog:
            self.device_config_dialog.update_device_maps(
                self.input_device_map, 
                self.output_device_map, 
                self.midi_device_map
            )
        
        # Load device settings and determine which devices to use
        self.determine_devices_from_settings()
        
        # Start MIDI listening and audio streaming
        self.start_devices()
        
        # Initialize spectrum analyzer and piano roll now that we're ready
        self.initialize_visualization_widgets()
    
    def populate_device_maps(self, input_devices, output_devices, midi_devices):
        """Populate device mappings from loaded devices"""
        # Clear existing mappings
        self.input_device_map.clear()
        self.output_device_map.clear()
        self.midi_device_map.clear()
        
        # Populate input devices
        for device in input_devices:
            display_name = f"{device.name} ({device.hostapi_name})"
            self.input_device_map[display_name] = device
        
        # Populate output devices - always include "Default Output"
        self.output_device_map["Default Output"] = "Default Output"
        for device in output_devices:
            display_name = f"{device.name} ({device.hostapi_name})"
            self.output_device_map[display_name] = device
        
        # Populate MIDI devices - always include "No MIDI"
        self.midi_device_map["No MIDI"] = None
        for device in midi_devices:
            self.midi_device_map[device.name] = device
    
    def determine_devices_from_settings(self):
        """Determine which devices to use based on settings or fallback to defaults"""
        # Determine input device
        last_input_display_name = self.settings_manager.get_last_input_device()
        
        self.current_input_device = None
        if last_input_display_name:
            # Try to find the device by display name first
            if last_input_display_name in self.input_device_map:
                self.current_input_device = self.input_device_map[last_input_display_name]
            else:
                # Try to find by partial name match (in case API suffix changed)
                for display_name, device in self.input_device_map.items():
                    if device and last_input_display_name in display_name:
                        self.current_input_device = device
                        break
        
        # Fallback to first available input device
        if not self.current_input_device and self.input_device_map:
            first_device_name = next(iter(self.input_device_map.keys()))
            self.current_input_device = self.input_device_map[first_device_name]
        
        # Determine output device
        last_output_display_name = self.settings_manager.get_last_output_device()
        
        self.current_output_device = "Default Output"  # Default fallback
        if last_output_display_name and last_output_display_name in self.output_device_map:
            self.current_output_device = self.output_device_map[last_output_display_name]
        
        # Determine MIDI device
        last_midi_display_name = self.settings_manager.get_last_midi_device()
        
        self.current_midi_device = None  # Default fallback (No MIDI)
        if last_midi_display_name and last_midi_display_name in self.midi_device_map:
            self.current_midi_device = self.midi_device_map[last_midi_display_name]
    
    def start_devices(self):
        """Start MIDI listening and audio streaming with determined devices"""
        # Start MIDI listening if device is selected
        if self.current_midi_device:
            success = self.midi_manager.start_listening(self.current_midi_device)
            if not success:
                self.current_midi_device = None  # Reset on failure
        
        # Start audio streaming
        self.try_start_streaming()
    
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
                self.spectrum_analyzer.fullscreen = self.isFullScreen()  # Set fullscreen state
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
                
                self.piano_roll = PianoRollWidget(parent=central_widget, settings_manager=self.settings_manager)
                self.piano_roll.fullscreen = self.isFullScreen()
                self.piano_roll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                self.piano_roll.setMinimumHeight(200)
                
                # Connect MIDI signals
                self.midi_manager.note_on.connect(self.piano_roll.add_note_on)
                self.midi_manager.note_off.connect(self.piano_roll.add_note_off)
                
                # Apply saved scroll speed to the newly created piano roll
                saved_speed = self.settings_manager.get_scroll_speed()
                self.piano_roll.set_scroll_speed(float(saved_speed))
                
            except Exception as e:
                print(f"Failed to initialize piano roll: {e}")
        
        # Update visualization widget based on current setting
        self.update_visualization_widget()
    
    def on_device_load_error(self, error_message):
        """Handle error loading devices"""
        print(f"Device loading failed: {error_message}")
        self.show_error(f"Failed to load devices: {error_message}")
    

    def setup_ui(self):
        """Setup the user interface"""
        self.setMinimumSize(900, 400)  # Reduced minimum size since we removed device rows
        self.resize(1024, 720)  # Reduced default size
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        self.root_layout = layout  # Store reference to root layout for later use
        layout.setSpacing(0)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Single toolbar row with all controls
        self.toolbar = QWidget()
        self.toolbar.setContentsMargins(0, 0, 0, 12)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setStyleSheet("""#toolbar { border-radius: 8px; }""")
        toolbar_row = QHBoxLayout(self.toolbar)
        toolbar_row.setSpacing(8)
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        
        # Left-aligned controls: streaming/mute, spectrum, particles
        
        # Combined status/mute button
        self.mute_button = QPushButton("Stopped")
        self.mute_button.setObjectName("status_mute_button")
        self.mute_button.setFixedSize(80, 30)
        self.mute_button.setProperty("muted", False)
        self.mute_button.setToolTip("Click to mute/unmute")
        toolbar_row.addWidget(self.mute_button)
        
        # View toggle button (spectrum/piano roll)
        self.view_toggle_button = QPushButton("Piano Roll")
        self.view_toggle_button.setFixedSize(80, 30)
        self.view_toggle_button.setToolTip("Switch between spectrum analyzer and piano roll")
        toolbar_row.addWidget(self.view_toggle_button)
        
        # Piano Roll configuration button
        self.particles_button = QPushButton("Settings")
        self.particles_button.setFixedSize(75, 30)  # Increased width from 70 to 85
        self.particles_button.setToolTip("Configure piano roll effects and gradients")
        self.particles_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d4a2d;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        toolbar_row.addWidget(self.particles_button)
        
        # Devices button
        self.devices_button = QPushButton("Devices")
        self.devices_button.setFixedSize(70, 30)
        self.devices_button.setToolTip("Configure audio and MIDI devices")
        self.devices_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d4a;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        toolbar_row.addWidget(self.devices_button)
        
        # Add stretch to push right-aligned controls to the right
        toolbar_row.addStretch()
        
        # Right-aligned controls: pause, clear, speed, delay
        
        # Piano roll control buttons
        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.setFixedSize(60, 30)
        self.play_pause_button.setToolTip("Play/Pause piano roll")
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #353535;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        toolbar_row.addWidget(self.play_pause_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFixedSize(50, 30)
        self.clear_button.setToolTip("Clear all notes")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a2d2d;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        toolbar_row.addWidget(self.clear_button)

        # Scroll speed control
        self.scroll_speed_input = QComboBox()
        self.scroll_speed_input.addItems(["Slower", "Slow", "Normal", "Fast", "Faster"])
        self.scroll_speed_input.setCurrentText("Normal")  # Default to normal speed
        self.scroll_speed_input.setMinimumHeight(30)
        self.scroll_speed_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.scroll_speed_input.setFixedWidth(80)
        self.scroll_speed_input.setToolTip("Piano roll scroll speed")
        toolbar_row.addWidget(self.scroll_speed_input)
        
        # MIDI delay control
        self.midi_delay_input = QSpinBox()
        self.midi_delay_input.setMinimum(0)
        self.midi_delay_input.setMaximum(1000)
        self.midi_delay_input.setValue(0)
        self.midi_delay_input.setSuffix(" ms")
        self.midi_delay_input.setMinimumHeight(30)
        self.midi_delay_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.midi_delay_input.setFixedWidth(80)
        self.midi_delay_input.setToolTip("MIDI delay compensation (milliseconds)")
        # Style to match QComboBox from theme
        self.midi_delay_input.setStyleSheet("""
            QSpinBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 9pt;
                min-height: 18px;
                max-height: 30px;
                border-style: solid;
                outline: none;
            }
            QSpinBox:hover {
                border-color: #0078d4;
                background-color: #454545;
            }
            QSpinBox:focus {
                border-color: #0078d4;
                background-color: #454545;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                border: none;
                background: transparent;
            }
        """)
        toolbar_row.addWidget(self.midi_delay_input)
        
        layout.addWidget(self.toolbar)
        
        visualizer_widget = QWidget()
        visualizer_widget.setContentsMargins(0, 0, 0, 0)
        visualizer_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.visualizer_layout = QVBoxLayout(visualizer_widget)
        self.visualizer_layout.setSpacing(0)
        self.visualizer_layout.setContentsMargins(0, 0, 0, 0)
        # self.visualizer_layout

        # Placeholder for visualization widgets - will be replaced with actual widgets when needed
        self.spectrum_placeholder = QLabel("Loading visualization...")
        self.spectrum_placeholder.setMinimumHeight(120)
        self.spectrum_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.spectrum_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spectrum_placeholder.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #888;
            font-size: 12px;
        """)
        self.visualizer_layout.addWidget(self.spectrum_placeholder, 1)
        
        layout.addWidget(visualizer_widget)
        
        # Initialize device combo boxes for internal use (not displayed)
        self.input_device_combo = QComboBox()
        self.input_device_combo.addItem("Loading input devices...")
        self.input_device_combo.setEnabled(False)
        
        self.output_device_combo = QComboBox()
        self.output_device_combo.addItem("Loading output devices...")
        self.output_device_combo.setEnabled(False)
        
        self.midi_device_combo = QComboBox()
        self.midi_device_combo.addItem("Loading MIDI devices...")
        self.midi_device_combo.setEnabled(False)

        
        # Will be replaced later
        self.spectrum_analyzer = None
        self.piano_roll = None
        self.keyboard_visualizer = None

        try:
            from .keyboard_visualizer import KeyboardVisualizer
            
            self.keyboard_visualizer = KeyboardVisualizer(parent=self.centralWidget(), settings_manager=self.settings_manager)
            self.keyboard_visualizer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.keyboard_visualizer.fullscreen = self.isFullScreen()  # Set fullscreen state
            self.keyboard_visualizer.setMinimumHeight(50)
            layout.addWidget(self.keyboard_visualizer)

            # Connect MIDI signals to the keyboard visualizer
            self.midi_manager.note_on.connect(self.keyboard_visualizer.highlight_key_on)
            self.midi_manager.note_off.connect(self.keyboard_visualizer.highlight_key_off)
        
        except Exception as e:
            print(f"Failed to initialize keyboard visualizer: {e}")
    
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
        
        # UI signals - only non-device controls
        self.scroll_speed_input.currentTextChanged.connect(self.on_scroll_speed_changed)
        self.midi_delay_input.valueChanged.connect(self.on_midi_delay_changed)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.view_toggle_button.clicked.connect(self.toggle_visualization)
        self.play_pause_button.clicked.connect(self.toggle_piano_roll_playback)
        self.clear_button.clicked.connect(self.clear_piano_roll)
        self.particles_button.clicked.connect(self.open_particle_config)
        self.devices_button.clicked.connect(self.open_device_config)
        
        # Keyboard shortcuts
        self.demo_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F8), self)
        self.demo_shortcut.activated.connect(self.start_demo_mode)
        self.reload_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F5), self)
        self.reload_shortcut.activated.connect(self.start_device_loading)
        self.fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        self.toolbar_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F9), self)
        self.toolbar_shortcut.activated.connect(self.toggle_toolbar)
    
    def on_input_device_changed(self, display_name: str):
        """Handle input device selection change from device dialog"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error") or display_name == "No input devices found":
            return
        
        # Get device from mapping
        new_device = self.input_device_map.get(display_name)
        
        if new_device and new_device != self.current_input_device:
            self.current_input_device = new_device
            
            # Save the device selection
            self.settings_manager.set_last_input_device(display_name)  # Save display name
            self.settings_manager.save_settings()
            
            # Restart streaming with new device
            self.restart_streaming()
    
    def on_output_device_changed(self, display_name: str):
        """Handle output device selection change from device dialog"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error"):
            return
        
        # Get device from mapping (can be device object or "Default Output")
        new_device = self.output_device_map.get(display_name)
        
        if new_device != self.current_output_device:
            self.current_output_device = new_device
            
            # Save the device selection
            self.settings_manager.set_last_output_device(display_name)
            self.settings_manager.save_settings()
            
            # Restart streaming with new device
            self.restart_streaming()
    
    def on_midi_device_changed(self, display_name: str):
        """Handle MIDI device selection change from device dialog"""
        if not display_name or display_name.startswith("Loading") or display_name.startswith("Error"):
            return
        
        # Get device from mapping
        new_device = self.midi_device_map.get(display_name)
        
        if new_device != self.current_midi_device:
            # Stop current MIDI listening
            self.midi_manager.stop_listening()
            
            self.current_midi_device = new_device
            
            # Start new MIDI listening if device is selected
            if new_device:
                success = self.midi_manager.start_listening(new_device)
                if success:
                    self.settings_manager.set_last_midi_device(display_name)
                    self.settings_manager.save_settings()
                else:
                    self.current_midi_device = None  # Reset on failure
            else:
                # "No MIDI" selected
                self.settings_manager.set_last_midi_device("")
                self.settings_manager.save_settings()
    
    def restart_streaming(self):
        """Restart audio streaming with current devices"""
        self.audio_manager.stop_streaming()
        self.try_start_streaming()
    
    def on_scroll_speed_changed(self, speed_text: str):
        """Handle scroll speed change"""
        # Convert text selection to speed value
        speed_map = {
            "Slower": 50,
            "Slow": 75,
            "Normal": 100,
            "Fast": 200,
            "Faster": 400
        }
        
        speed = speed_map.get(speed_text, 100)  # Default to 100 if not found
        
        if self.piano_roll:
            self.piano_roll.set_scroll_speed(float(speed))
        
        # Save the scroll speed setting
        self.settings_manager.set_scroll_speed(speed)
        self.settings_manager.save_settings()
    
    def on_midi_delay_changed(self, delay_ms: int):
        """Handle MIDI delay change"""
        if self.midi_manager:
            self.midi_manager.set_delay(delay_ms)
        
        # Save the MIDI delay setting
        self.settings_manager.set_midi_delay(delay_ms)
        self.settings_manager.save_settings()
    
    def toggle_piano_roll_playback(self):
        """Toggle piano roll play/pause state"""
        if self.piano_roll:
            self.piano_roll.toggle_pause()
            # Update button text based on current state
            if self.piano_roll.is_playing():
                self.play_pause_button.setText("Pause")
                self.play_pause_button.setToolTip("Pause piano roll")
            else:
                self.play_pause_button.setText("Play")
                self.play_pause_button.setToolTip("Play piano roll")
    
    def clear_piano_roll(self):
        """Clear all notes from the piano roll"""
        if self.piano_roll:
            self.piano_roll.clear_notes()
    
    def start_demo_mode(self):
        """Start demo mode that plays a sequence of notes (triggered by F8)"""
        # Switch to piano roll view if not already active
        if not self.show_piano_roll:
            self.toggle_visualization()
        
        # Provide visual feedback in the window title
        original_title = self.windowTitle()
        self.setWindowTitle("Midivis (Playing Demo...)")
        
        # Start the demo sequence
        self.midi_manager.start_demo_mode()
        
        # Restore title after demo duration (approximately 10 seconds)
        QTimer.singleShot(10000, lambda: self.setWindowTitle(original_title))
        
    def enable_fullscreen(self):
        self.setWindowState(self.windowState() | Qt.WindowState.WindowFullScreen)
        self.root_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins in fullscreen
        self.root_layout.removeWidget(self.toolbar)
        # Reparent and make floating
        self.toolbar.setParent(self)
        self.toolbar.raise_()
        self.toolbar.setGeometry(12, 12, self.width() - 24, 50)
        self.toolbar.setContentsMargins(8, 8, 8, 8)
        self.toolbar.show()
        self.piano_roll.fullscreen = True
        self.keyboard_visualizer.fullscreen = True
        self.spectrum_analyzer.fullscreen = True
        
    def disable_fullscreen(self):
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowFullScreen)
        self.root_layout.setContentsMargins(12, 12, 12, 12) # Remove margins in fullscreen
        # Restore toolbar to layout
        self.toolbar.setParent(self)
        self.toolbar.setContentsMargins(0, 0, 0, 12)
        self.root_layout.insertWidget(0, self.toolbar)
        self.piano_roll.fullscreen = False
        self.keyboard_visualizer.fullscreen = False
        self.spectrum_analyzer.fullscreen = False
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.disable_fullscreen()
        else:
            self.enable_fullscreen()
            
            
    def toggle_toolbar(self):
        if self.toolbar.isVisible():
            self.toolbar.hide()
        else:
            self.toolbar.show()

    def open_particle_config(self):
        """Open the piano roll configuration dialog"""
        if not self.piano_roll:
            return
        
        try:
            # Import the piano roll config dialog
            from .particle_config_dialog import PianoRollConfigDialog
        except ImportError:
            from ui.particle_config_dialog import PianoRollConfigDialog
        
        # Create and show the dialog
        dialog = PianoRollConfigDialog(self.piano_roll, self)
        dialog.show()
    
    def open_device_config(self):
        """Open the device configuration dialog"""
        if not self.devices_loaded:
            QMessageBox.information(self, "Devices Loading", 
                                   "Devices are still loading. Please wait a moment and try again.")
            return
        
        try:
            # Import the device config dialog
            from .device_config_dialog import DeviceConfigDialog
        except ImportError:
            from ui.device_config_dialog import DeviceConfigDialog
        
        # Create the dialog if it doesn't exist
        if not self.device_config_dialog:
            self.device_config_dialog = DeviceConfigDialog(
                self.input_device_map, 
                self.output_device_map, 
                self.midi_device_map, 
                self
            )
            
            # Connect signals
            self.device_config_dialog.input_device_changed.connect(self.on_input_device_changed)
            self.device_config_dialog.output_device_changed.connect(self.on_output_device_changed)
            self.device_config_dialog.midi_device_changed.connect(self.on_midi_device_changed)
            self.device_config_dialog.refresh_devices_requested.connect(self.refresh_devices)
        else:
            # Update device maps in existing dialog
            self.device_config_dialog.update_device_maps(
                self.input_device_map, 
                self.output_device_map, 
                self.midi_device_map
            )
        
        # Always set current device selections in the dialog (this ensures sync)
        current_input = None
        current_output = None
        current_midi = None
        
        # Find display names for current devices
        if self.current_input_device:
            for display_name, device in self.input_device_map.items():
                if device == self.current_input_device:
                    current_input = display_name
                    break
        
        if self.current_output_device:
            if self.current_output_device == "Default Output":
                current_output = "Default Output"
            else:
                for display_name, device in self.output_device_map.items():
                    if device == self.current_output_device:
                        current_output = display_name
                        break
        
        if self.current_midi_device:
            for display_name, device in self.midi_device_map.items():
                if device == self.current_midi_device:
                    current_midi = display_name
                    break
        else:
            current_midi = "No MIDI"
        
        self.device_config_dialog.set_current_devices(current_input, current_output, current_midi)
        
        # Show the dialog
        self.device_config_dialog.show()
        self.device_config_dialog.raise_()
        self.device_config_dialog.activateWindow()
    
    def refresh_devices(self):
        """Refresh all devices (called from device config dialog)"""
        if self.device_worker and self.device_worker.isRunning():
            return  # Already refreshing
        
        # Restart device loading
        self.devices_loaded = False
        self.start_device_loading()
    
    def try_start_streaming(self):
        """Try to start streaming with current devices"""
        if not self.devices_loaded or not self.current_input_device:
            return
        
        # Determine the actual output device to pass to audio manager
        output_device = None if self.current_output_device == "Default Output" else self.current_output_device
        
        self.audio_manager.start_streaming(self.current_input_device, output_device)
    
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
        self.setWindowTitle(f"Midivis - {message}")
    
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
                screen_geometry = QApplication.primaryScreen().geometry()
                if self.geometry() == screen_geometry:
                    self.enable_fullscreen()
            except:
                pass  # Ignore geometry restore errors
        
        # Load other preferences that don't depend on devices
        self.load_ui_preferences()
    
    def load_ui_preferences(self):
        """Load UI preferences that don't depend on devices"""
        # Load view preference
        self.show_piano_roll = self.settings_manager.get_show_piano_roll()
        
        # Load scroll speed preference
        saved_speed = self.settings_manager.get_scroll_speed()
        speed_text_map = {
            50: "Slower",
            75: "Slow", 
            100: "Normal",
            200: "Fast",
            400: "Faster"
        }
        speed_text = speed_text_map.get(saved_speed, "Normal")
        self.scroll_speed_input.setCurrentText(speed_text)
        
        # Apply the saved scroll speed to the piano roll widget
        if self.piano_roll:
            self.piano_roll.set_scroll_speed(float(saved_speed))
        
        # Load MIDI delay preference
        saved_delay = self.settings_manager.get_midi_delay()
        self.midi_delay_input.setValue(saved_delay)
    
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
        # layout = self.centralWidget().layout()
        layout = self.visualizer_layout
        
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
                self.keyboard_visualizer.show()
                layout.removeWidget(current_widget)
                current_widget.hide()
                current_widget.setParent(None)
                
                # Add piano roll
                layout.addWidget(self.piano_roll, 1)
                self.piano_roll.show()
                self.piano_roll.raise_()
                
                # Update button text
                self.view_toggle_button.setText("Spectrum")
                
                # Update play/pause button state based on piano roll state
                if self.piano_roll.is_playing():
                    self.play_pause_button.setText("Pause")
                    self.play_pause_button.setToolTip("Pause piano roll")
                else:
                    self.play_pause_button.setText("Play")
                    self.play_pause_button.setToolTip("Play piano roll")
        
        # Handle switch to spectrum analyzer
        else:
            if not self.spectrum_analyzer:
                return
                
            if current_widget != self.spectrum_analyzer:
                # Replace current widget with spectrum analyzer
                self.keyboard_visualizer.hide()
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
    
    def resizeEvent(self, event):
        """Adjust the keyboard visualizer height to 10% of the window height."""
        super().resizeEvent(event)
        if self.keyboard_visualizer:
            new_height = int(self.height() * 0.1)  # 10% of the window height
            self.keyboard_visualizer.setFixedHeight(new_height)
