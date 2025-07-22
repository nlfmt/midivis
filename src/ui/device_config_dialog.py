from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFrame, QMessageBox, QSizePolicy, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class DeviceConfigDialog(QDialog):
    """Dialog for configuring audio input, output, and MIDI devices"""
    
    # Signals emitted when devices change
    input_device_changed = Signal(str)  # display_name
    output_device_changed = Signal(str)  # display_name
    midi_device_changed = Signal(str)   # display_name
    refresh_devices_requested = Signal()  # Request to refresh all devices
    
    def __init__(self, input_device_map, output_device_map, midi_device_map, parent=None):
        super().__init__(parent)
        
        # Device mappings
        self.input_device_map = input_device_map
        self.output_device_map = output_device_map
        self.midi_device_map = midi_device_map
        
        # Store current selections
        self.current_input_device = None
        self.current_output_device = None
        self.current_midi_device = None
        
        # Flag to prevent signal emission during initial setup
        self.loading = True
        
        self.setup_ui()
        self.setup_connections()
        self.populate_device_combos()
        
        # Enable signal emission now that setup is complete
        self.loading = False
        
        # Apply custom styling
        self.apply_styles()
        
        # Force background color update with palette
        from PySide6.QtGui import QPalette, QColor
        palette = QPalette()
        dark_gray = QColor(43, 43, 43)  # #2b2b2b
        palette.setColor(QPalette.ColorRole.Window, dark_gray)
        palette.setColor(QPalette.ColorRole.Base, dark_gray)
        palette.setColor(QPalette.ColorRole.AlternateBase, dark_gray)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Device Configuration")
        self.setModal(True)
        self.setMinimumSize(550, 240)  # Taller to prevent text cutoff
        self.resize(600, 260)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Remove the large title - window title is enough
        
        # Input device section
        input_section = self.create_device_section("Audio Input Device", "input")
        layout.addWidget(input_section)
        
        # Output device section
        output_section = self.create_device_section("Audio Output Device", "output")
        layout.addWidget(output_section)
        
        # MIDI device section
        midi_section = self.create_device_section("MIDI Input Device", "midi")
        layout.addWidget(midi_section)
    
    def create_device_section(self, title, device_type):
        """Create a device selection section"""
        # Create a simple widget instead of a frame
        section_widget = QWidget()
        
        layout = QVBoxLayout(section_widget)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)  # No extra padding
        
        # Section title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Device selector row - label and combo on same row
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(8)
        
        # Create combo box
        combo = QComboBox()
        combo.setMinimumHeight(30)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Store combo box reference
        if device_type == "input":
            self.input_device_combo = combo
            combo.setPlaceholderText("Select audio input device...")
        elif device_type == "output":
            self.output_device_combo = combo
            combo.setPlaceholderText("Select audio output device...")
        elif device_type == "midi":
            self.midi_device_combo = combo
            combo.setPlaceholderText("Select MIDI input device...")
        
        selector_layout.addWidget(combo, 1)
        
        # Refresh button for this device type
        refresh_button = QPushButton("Refresh")
        refresh_button.setMinimumHeight(30)
        refresh_button.setFixedWidth(85)  # Wider to fit text properly
        refresh_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Store refresh button reference
        if device_type == "input":
            self.input_refresh_button = refresh_button
        elif device_type == "output":
            self.output_refresh_button = refresh_button
        elif device_type == "midi":
            self.midi_refresh_button = refresh_button
        
        selector_layout.addWidget(refresh_button)
        
        layout.addLayout(selector_layout)
        
        return section_widget
    
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Device combo box changes
        self.input_device_combo.currentTextChanged.connect(
            lambda text: self.on_device_changed(text, "input"))
        self.output_device_combo.currentTextChanged.connect(
            lambda text: self.on_device_changed(text, "output"))
        self.midi_device_combo.currentTextChanged.connect(
            lambda text: self.on_device_changed(text, "midi"))
        
        # Refresh buttons
        self.input_refresh_button.clicked.connect(
            lambda: self.refresh_devices_requested.emit())
        self.output_refresh_button.clicked.connect(
            lambda: self.refresh_devices_requested.emit())
        self.midi_refresh_button.clicked.connect(
            lambda: self.refresh_devices_requested.emit())
    
    def on_device_changed(self, display_name, device_type):
        """Handle device selection change"""
        if self.loading or not display_name or display_name.startswith("Loading") or display_name.startswith("Error"):
            return
        
        # Store current selection
        if device_type == "input":
            self.current_input_device = display_name
            self.input_device_changed.emit(display_name)
        elif device_type == "output":
            self.current_output_device = display_name
            self.output_device_changed.emit(display_name)
        elif device_type == "midi":
            self.current_midi_device = display_name
            self.midi_device_changed.emit(display_name)
    
    def populate_device_combos(self):
        """Populate all device combo boxes"""
        self.populate_input_devices()
        self.populate_output_devices()
        self.populate_midi_devices()
    
    def populate_input_devices(self):
        """Populate the input device combo box"""
        self.input_device_combo.clear()
        self.input_device_combo.setEnabled(True)
        
        if not self.input_device_map:
            self.input_device_combo.addItem("No input devices found")
            self.input_device_combo.setEnabled(False)
        else:
            for display_name in self.input_device_map.keys():
                self.input_device_combo.addItem(display_name)
    
    def populate_output_devices(self):
        """Populate the output device combo box"""
        self.output_device_combo.clear()
        self.output_device_combo.setEnabled(True)
        
        # Always add "Default Output" first
        self.output_device_combo.addItem("Default Output")
        
        # Add other output devices
        for display_name in self.output_device_map.keys():
            if display_name != "Default Output":  # Avoid duplicates
                self.output_device_combo.addItem(display_name)
    
    def populate_midi_devices(self):
        """Populate the MIDI device combo box"""
        self.midi_device_combo.clear()
        self.midi_device_combo.setEnabled(True)
        
        # Always add "No MIDI" first
        self.midi_device_combo.addItem("No MIDI")
        
        # Add MIDI devices (skip "No MIDI" to avoid duplicates)
        for display_name in self.midi_device_map.keys():
            if display_name != "No MIDI":
                self.midi_device_combo.addItem(display_name)
    
    def update_device_maps(self, input_device_map, output_device_map, midi_device_map):
        """Update device mappings and repopulate combo boxes"""
        self.loading = True  # Prevent signals during update
        
        self.input_device_map = input_device_map
        self.output_device_map = output_device_map
        self.midi_device_map = midi_device_map
        
        # Store current selections before repopulating
        current_input = self.input_device_combo.currentText()
        current_output = self.output_device_combo.currentText()
        current_midi = self.midi_device_combo.currentText()
        
        # Repopulate combo boxes
        self.populate_device_combos()
        
        # Restore selections if they still exist
        if current_input and self.input_device_combo.findText(current_input) >= 0:
            self.input_device_combo.setCurrentText(current_input)
        
        if current_output and self.output_device_combo.findText(current_output) >= 0:
            self.output_device_combo.setCurrentText(current_output)
            
        if current_midi and self.midi_device_combo.findText(current_midi) >= 0:
            self.midi_device_combo.setCurrentText(current_midi)
        
        self.loading = False  # Re-enable signals
    
    def set_current_devices(self, input_device, output_device, midi_device):
        """Set the currently selected devices in the combo boxes"""
        self.loading = True  # Prevent signals during update
        
        if input_device and self.input_device_combo.findText(input_device) >= 0:
            self.input_device_combo.setCurrentText(input_device)
            
        if output_device and self.output_device_combo.findText(output_device) >= 0:
            self.output_device_combo.setCurrentText(output_device)
            
        if midi_device and self.midi_device_combo.findText(midi_device) >= 0:
            self.midi_device_combo.setCurrentText(midi_device)
        
        self.loading = False  # Re-enable signals
    
    def apply_styles(self):
        """Apply custom styling to the dialog"""
        style = """
        QDialog {
            background-color: #2b2b2b;  /* Dark gray to match main UI and particle dialog */
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;  /* Ensure all widgets have consistent background */
        }
        
        QLabel {
            color: #ffffff;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        }
        
        QComboBox {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px 12px;
            color: #ffffff;
            font-size: 10pt;
            min-height: 18px;
            selection-background-color: #0078d4;
        }
        
        QComboBox:hover {
            border-color: #0078d4;
            background-color: #454545;
        }
        
        QComboBox:focus {
            border-color: #0078d4;
            background-color: #454545;
            outline: none;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
            padding-right: 8px;
        }
        
        QComboBox::down-arrow {
            width: 0px;
            height: 0px;
            border: none;
            background: transparent;
        }
        
        QComboBox QAbstractItemView {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
            selection-background-color: #0078d4;
            outline: none;
        }
        
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px 16px;
            color: #ffffff;
            font-size: 10pt;
            font-weight: normal;  /* Not bold */
        }
        
        QPushButton:hover {
            background-color: #4a4a4a;
            border-color: #0078d4;
        }
        
        QPushButton:pressed {
            background-color: #353535;
        }
        
        QPushButton:focus {
            border-color: #0078d4;
            outline: none;
        }
        """
        
        self.setStyleSheet(style)
