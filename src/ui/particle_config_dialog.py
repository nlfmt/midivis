from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QSpinBox, QDoubleSpinBox, QCheckBox, 
                               QPushButton, QGroupBox, QGridLayout, QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen
from vcolorpicker import getColor


class ColorDisplay(QWidget):
    """Clickable widget to display a color as a rounded rectangle"""
    
    # Signal emitted when the color display is clicked
    clicked = Signal()
    
    def __init__(self, color=(255, 255, 255), parent=None):
        super().__init__(parent)
        self.color = QColor(*color)
        self.setFixedSize(120, 35)
        self.setToolTip(f"RGB: {color[0]}, {color[1]}, {color[2]}\nClick to change color")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setColor(self, color):
        """Set the color from RGB tuple"""
        if isinstance(color, tuple) and len(color) >= 3:
            self.color = QColor(color[0], color[1], color[2])
            self.setToolTip(f"RGB: {color[0]}, {color[1]}, {color[2]}\nClick to change color")
            self.update()
    
    def getColor(self):
        """Get the color as RGB tuple"""
        return (self.color.red(), self.color.green(), self.color.blue())
    
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        """Paint the color rectangle with improved antialiasing"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Draw rounded rectangle with the color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        
        # Draw a subtle border with antialiasing
        painter.setPen(QPen(QColor(128, 128, 128), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)


class PianoRollConfigDialog(QDialog):
    """Dialog for configuring piano roll parameters including particles and gradients"""
    
    def __init__(self, piano_roll, parent=None):
        super().__init__(parent)
        self.piano_roll = piano_roll
        self.setWindowTitle("Piano Roll Configuration")
        self.setMinimumSize(450, 500)
        self.resize(500, 650)
        
        # Store original config for reset functionality
        self.original_config = piano_roll.get_particle_config()
        
        # Set custom stylesheet for the dialog - make it specific to avoid affecting child dialogs
        self.setStyleSheet("""
            PianoRollConfigDialog {
                background-color: #2b2b2b;  /* Dark gray to match main UI and device dialog */
                color: #ffffff;
            }
            
            PianoRollConfigDialog QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            PianoRollConfigDialog QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            PianoRollConfigDialog QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            PianoRollConfigDialog QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            
            PianoRollConfigDialog QScrollBar::handle:vertical:pressed {
                background-color: #777777;
            }
            
            PianoRollConfigDialog QScrollBar::add-line:vertical,
            PianoRollConfigDialog QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            
            PianoRollConfigDialog QScrollBar::add-page:vertical,
            PianoRollConfigDialog QScrollBar::sub-page:vertical {
                background: none;
            }
            
            PianoRollConfigDialog QSpinBox::up-button,
            PianoRollConfigDialog QSpinBox::down-button,
            PianoRollConfigDialog QDoubleSpinBox::up-button,
            PianoRollConfigDialog QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
                background: none;
            }
            
            PianoRollConfigDialog QSpinBox,
            PianoRollConfigDialog QDoubleSpinBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px 6px;
                color: #ffffff;
                min-width: 50px;
                max-width: 70px;
                font-size: 9pt;
            }
            
            PianoRollConfigDialog QSpinBox:focus,
            PianoRollConfigDialog QDoubleSpinBox:focus {
                border-color: #0078d4;
            }
            
            PianoRollConfigDialog QLabel {
                border: none;
                background: none;
                color: #ffffff;
                font-size: 9pt;
                padding: 1px;
                margin: 1px;
            }
            
            PianoRollConfigDialog QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                margin-bottom: 4px;
            }
            
            PianoRollConfigDialog QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: #ffffff;
                font-size: 10pt;
            }
            
            PianoRollConfigDialog QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 6px;
                background: #404040;
                border-radius: 3px;
                margin: 2px 0;
            }
            
            PianoRollConfigDialog QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #0078d4;
                width: 14px;
                margin: -3px 0;
                border-radius: 7px;
            }
            
            PianoRollConfigDialog QSlider::handle:horizontal:hover {
                background: #106ebe;
            }
            
            PianoRollConfigDialog QCheckBox {
                color: #ffffff;
                font-size: 9pt;
                padding: 2px;
                margin: 2px;
            }
            
            PianoRollConfigDialog QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            PianoRollConfigDialog QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            
            PianoRollConfigDialog QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 3px;
            }
            
            PianoRollConfigDialog QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 12px;
                font-size: 9pt;
                min-height: 16px;
            }
            
            PianoRollConfigDialog QPushButton:hover {
                background-color: #106ebe;
            }
            
            PianoRollConfigDialog QPushButton:pressed {
                background-color: #005a9e;
            }
            
            PianoRollConfigDialog QPushButton#reset_button {
                background-color: #7d2d2d;
            }
            
            PianoRollConfigDialog QPushButton#reset_button:hover {
                background-color: #9d3d3d;
            }
        """)
        
        # Setup UI
        self.setup_ui()
        self.load_current_values()
    
    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)
        
        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # Main enable/disable checkbox
        enable_group = QGroupBox("Particle System")
        enable_layout = QVBoxLayout(enable_group)
        enable_layout.setContentsMargins(8, 12, 8, 8)
        enable_layout.setSpacing(4)
        
        self.particles_enabled_cb = QCheckBox("Enable Particle Effects")
        self.particles_enabled_cb.stateChanged.connect(self.on_particles_enabled_changed)
        enable_layout.addWidget(self.particles_enabled_cb)
        
        layout.addWidget(enable_group)
        
        # Regular Particles Group
        particles_group = QGroupBox("Regular Particles")
        particles_layout = QGridLayout(particles_group)
        particles_layout.setContentsMargins(8, 12, 8, 8)
        particles_layout.setSpacing(4)
        particles_layout.setVerticalSpacing(6)
        
        row = 0
        
        # Spawn Rate
        particles_layout.addWidget(QLabel("Spawn Rate (s):"), row, 0)
        self.spawn_rate_slider = self.create_slider(0.001, 0.1, 0.01, 1000)
        self.spawn_rate_spinbox = QDoubleSpinBox()
        self.spawn_rate_spinbox.setRange(0.001, 0.1)
        self.spawn_rate_spinbox.setDecimals(3)
        self.spawn_rate_spinbox.setSingleStep(0.001)
        particles_layout.addWidget(self.spawn_rate_slider, row, 1)
        particles_layout.addWidget(self.spawn_rate_spinbox, row, 2)
        self.connect_slider_spinbox(self.spawn_rate_slider, self.spawn_rate_spinbox, 'spawn_rate')
        row += 1
        
        # Velocity X Range
        particles_layout.addWidget(QLabel("Velocity X Min:"), row, 0)
        self.vel_x_min_slider = self.create_slider(-50, 50, -5, 1)
        self.vel_x_min_spinbox = QDoubleSpinBox()
        self.vel_x_min_spinbox.setRange(-50, 50)
        self.vel_x_min_spinbox.setDecimals(1)
        particles_layout.addWidget(self.vel_x_min_slider, row, 1)
        particles_layout.addWidget(self.vel_x_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.vel_x_min_slider, self.vel_x_min_spinbox, 'initial_velocity_x_min')
        row += 1
        
        particles_layout.addWidget(QLabel("Velocity X Max:"), row, 0)
        self.vel_x_max_slider = self.create_slider(-50, 50, 5, 1)
        self.vel_x_max_spinbox = QDoubleSpinBox()
        self.vel_x_max_spinbox.setRange(-50, 50)
        self.vel_x_max_spinbox.setDecimals(1)
        particles_layout.addWidget(self.vel_x_max_slider, row, 1)
        particles_layout.addWidget(self.vel_x_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.vel_x_max_slider, self.vel_x_max_spinbox, 'initial_velocity_x_max')
        row += 1
        
        # Velocity Y Range
        particles_layout.addWidget(QLabel("Velocity Y Min:"), row, 0)
        self.vel_y_min_slider = self.create_slider(-200, 0, -80, 1)
        self.vel_y_min_spinbox = QDoubleSpinBox()
        self.vel_y_min_spinbox.setRange(-200, 0)
        self.vel_y_min_spinbox.setDecimals(1)
        particles_layout.addWidget(self.vel_y_min_slider, row, 1)
        particles_layout.addWidget(self.vel_y_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.vel_y_min_slider, self.vel_y_min_spinbox, 'initial_velocity_y_min')
        row += 1
        
        particles_layout.addWidget(QLabel("Velocity Y Max:"), row, 0)
        self.vel_y_max_slider = self.create_slider(-200, 0, -30, 1)
        self.vel_y_max_spinbox = QDoubleSpinBox()
        self.vel_y_max_spinbox.setRange(-200, 0)
        self.vel_y_max_spinbox.setDecimals(1)
        particles_layout.addWidget(self.vel_y_max_slider, row, 1)
        particles_layout.addWidget(self.vel_y_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.vel_y_max_slider, self.vel_y_max_spinbox, 'initial_velocity_y_max')
        row += 1
        
        # Size Range
        particles_layout.addWidget(QLabel("Size Min:"), row, 0)
        self.size_min_slider = self.create_slider(0.1, 3.0, 0.4, 10)
        self.size_min_spinbox = QDoubleSpinBox()
        self.size_min_spinbox.setRange(0.1, 3.0)
        self.size_min_spinbox.setDecimals(1)
        particles_layout.addWidget(self.size_min_slider, row, 1)
        particles_layout.addWidget(self.size_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.size_min_slider, self.size_min_spinbox, 'initial_size_min')
        row += 1
        
        particles_layout.addWidget(QLabel("Size Max:"), row, 0)
        self.size_max_slider = self.create_slider(0.1, 3.0, 0.8, 10)
        self.size_max_spinbox = QDoubleSpinBox()
        self.size_max_spinbox.setRange(0.1, 3.0)
        self.size_max_spinbox.setDecimals(1)
        particles_layout.addWidget(self.size_max_slider, row, 1)
        particles_layout.addWidget(self.size_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.size_max_slider, self.size_max_spinbox, 'initial_size_max')
        row += 1
        
        # Opacity Range
        particles_layout.addWidget(QLabel("Opacity Min:"), row, 0)
        self.opacity_min_slider = self.create_slider(0, 255, 40, 1)
        self.opacity_min_spinbox = QSpinBox()
        self.opacity_min_spinbox.setRange(0, 255)
        particles_layout.addWidget(self.opacity_min_slider, row, 1)
        particles_layout.addWidget(self.opacity_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.opacity_min_slider, self.opacity_min_spinbox, 'initial_opacity_min')
        row += 1
        
        particles_layout.addWidget(QLabel("Opacity Max:"), row, 0)
        self.opacity_max_slider = self.create_slider(0, 255, 80, 1)
        self.opacity_max_spinbox = QSpinBox()
        self.opacity_max_spinbox.setRange(0, 255)
        particles_layout.addWidget(self.opacity_max_slider, row, 1)
        particles_layout.addWidget(self.opacity_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.opacity_max_slider, self.opacity_max_spinbox, 'initial_opacity_max')
        row += 1
        
        # Life Range
        particles_layout.addWidget(QLabel("Life Min (s):"), row, 0)
        self.life_min_slider = self.create_slider(0.1, 10.0, 0.5, 10)
        self.life_min_spinbox = QDoubleSpinBox()
        self.life_min_spinbox.setRange(0.1, 10.0)
        self.life_min_spinbox.setDecimals(1)
        particles_layout.addWidget(self.life_min_slider, row, 1)
        particles_layout.addWidget(self.life_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.life_min_slider, self.life_min_spinbox, 'life_min')
        row += 1
        
        particles_layout.addWidget(QLabel("Life Max (s):"), row, 0)
        self.life_max_slider = self.create_slider(0.1, 10.0, 3.0, 10)
        self.life_max_spinbox = QDoubleSpinBox()
        self.life_max_spinbox.setRange(0.1, 10.0)
        self.life_max_spinbox.setDecimals(1)
        particles_layout.addWidget(self.life_max_slider, row, 1)
        particles_layout.addWidget(self.life_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.life_max_slider, self.life_max_spinbox, 'life_max')
        row += 1
        
        # Physics parameters
        particles_layout.addWidget(QLabel("Turbulence:"), row, 0)
        self.turbulence_slider = self.create_slider(0.0, 3.0, 0.8, 10)
        self.turbulence_spinbox = QDoubleSpinBox()
        self.turbulence_spinbox.setRange(0.0, 3.0)
        self.turbulence_spinbox.setDecimals(1)
        particles_layout.addWidget(self.turbulence_slider, row, 1)
        particles_layout.addWidget(self.turbulence_spinbox, row, 2)
        self.connect_slider_spinbox(self.turbulence_slider, self.turbulence_spinbox, 'turbulence_strength')
        row += 1
        
        particles_layout.addWidget(QLabel("Damping:"), row, 0)
        self.damping_slider = self.create_slider(0.8, 1.0, 0.995, 1000)
        self.damping_spinbox = QDoubleSpinBox()
        self.damping_spinbox.setRange(0.8, 1.0)
        self.damping_spinbox.setDecimals(3)
        self.damping_spinbox.setSingleStep(0.001)
        particles_layout.addWidget(self.damping_slider, row, 1)
        particles_layout.addWidget(self.damping_spinbox, row, 2)
        self.connect_slider_spinbox(self.damping_slider, self.damping_spinbox, 'damping_factor')
        row += 1
        
        layout.addWidget(particles_group)
        
        # Gradient Configuration Group
        gradient_group = QGroupBox("Note Color Gradient")
        gradient_layout = QGridLayout(gradient_group)
        gradient_layout.setContentsMargins(8, 12, 8, 8)
        gradient_layout.setSpacing(4)
        gradient_layout.setVerticalSpacing(6)
        
        row = 0
        
        # Gradient enable
        self.gradient_enabled_cb = QCheckBox("Enable Gradient Coloring")
        self.gradient_enabled_cb.stateChanged.connect(self.on_gradient_enabled_changed)
        gradient_layout.addWidget(self.gradient_enabled_cb, row, 0, 1, 3)
        row += 1
        
        # Color preset buttons with padding
        gradient_layout.addWidget(QLabel("Presets:"), row, 0)
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)  # Add padding between preset buttons
        
        self.preset_fire_button = QPushButton("Fire")
        self.preset_fire_button.setFixedHeight(25)
        self.preset_fire_button.clicked.connect(lambda: self.apply_gradient_preset("fire"))
        preset_layout.addWidget(self.preset_fire_button)
        
        self.preset_ocean_button = QPushButton("Ocean")
        self.preset_ocean_button.setFixedHeight(25)
        self.preset_ocean_button.clicked.connect(lambda: self.apply_gradient_preset("ocean"))
        preset_layout.addWidget(self.preset_ocean_button)
        
        self.preset_sunset_button = QPushButton("Sunset")
        self.preset_sunset_button.setFixedHeight(25)
        self.preset_sunset_button.clicked.connect(lambda: self.apply_gradient_preset("sunset"))
        preset_layout.addWidget(self.preset_sunset_button)
        
        self.preset_forest_button = QPushButton("Forest")
        self.preset_forest_button.setFixedHeight(25)
        self.preset_forest_button.clicked.connect(lambda: self.apply_gradient_preset("forest"))
        preset_layout.addWidget(self.preset_forest_button)
        
        # Second row of presets
        preset_layout_2 = QHBoxLayout()
        preset_layout_2.setSpacing(8)  # Add padding between preset buttons
        
        self.preset_emerald_button = QPushButton("Emerald")
        self.preset_emerald_button.setFixedHeight(25)
        self.preset_emerald_button.clicked.connect(lambda: self.apply_gradient_preset("emerald"))
        preset_layout_2.addWidget(self.preset_emerald_button)
        
        self.preset_gold_button = QPushButton("Gold")
        self.preset_gold_button.setFixedHeight(25)
        self.preset_gold_button.clicked.connect(lambda: self.apply_gradient_preset("gold"))
        preset_layout_2.addWidget(self.preset_gold_button)
        
        self.preset_citrus_button = QPushButton("Citrus")
        self.preset_citrus_button.setFixedHeight(25)
        self.preset_citrus_button.clicked.connect(lambda: self.apply_gradient_preset("citrus"))
        preset_layout_2.addWidget(self.preset_citrus_button)
        
        self.preset_purple_button = QPushButton("Purple")
        self.preset_purple_button.setFixedHeight(25)
        self.preset_purple_button.clicked.connect(lambda: self.apply_gradient_preset("purple"))
        preset_layout_2.addWidget(self.preset_purple_button)
        
        gradient_layout.addLayout(preset_layout, row, 1, 1, 2)
        row += 1
        gradient_layout.addLayout(preset_layout_2, row, 1, 1, 2)
        row += 1
        
        # Color picker controls - reordered to top, middle, bottom
        gradient_layout.addWidget(QLabel("Top Color:"), row, 0)
        self.top_color_display = ColorDisplay((255, 50, 50))
        self.top_color_display.clicked.connect(self.pick_top_color)
        gradient_layout.addWidget(self.top_color_display, row, 1)
        row += 1
        
        gradient_layout.addWidget(QLabel("Middle Color:"), row, 0)
        self.middle_color_display = ColorDisplay((255, 150, 0))
        self.middle_color_display.clicked.connect(self.pick_middle_color)
        gradient_layout.addWidget(self.middle_color_display, row, 1)
        row += 1
        
        gradient_layout.addWidget(QLabel("Bottom Color:"), row, 0)
        self.bottom_color_display = ColorDisplay((255, 100, 150))
        self.bottom_color_display.clicked.connect(self.pick_bottom_color)
        gradient_layout.addWidget(self.bottom_color_display, row, 1)
        row += 1
        
        layout.addWidget(gradient_group)
        
        # Visual Settings Group
        visual_group = QGroupBox("Visual Settings")
        visual_layout = QGridLayout(visual_group)
        visual_layout.setContentsMargins(8, 12, 8, 8)
        visual_layout.setSpacing(4)
        visual_layout.setVerticalSpacing(6)
        
        row = 0
        
        # Note labels checkbox
        self.show_note_labels_cb = QCheckBox("Show Note Labels (C4, D4, etc.)")
        self.show_note_labels_cb.stateChanged.connect(self.on_note_labels_changed)
        visual_layout.addWidget(self.show_note_labels_cb, row, 0, 1, 3)
        row += 1
        
        layout.addWidget(visual_group)
        
        # Spark Particles Group
        spark_group = QGroupBox("Spark Particles")
        spark_layout = QGridLayout(spark_group)
        spark_layout.setContentsMargins(8, 12, 8, 8)
        spark_layout.setSpacing(4)
        spark_layout.setVerticalSpacing(6)
        
        row = 0
        
        # Spark enable
        self.spark_enabled_cb = QCheckBox("Enable Spark Particles")
        self.spark_enabled_cb.stateChanged.connect(self.on_spark_enabled_changed)
        spark_layout.addWidget(self.spark_enabled_cb, row, 0, 1, 3)
        row += 1
        
        # Spark size range
        spark_layout.addWidget(QLabel("Spark Size Min:"), row, 0)
        self.spark_size_min_slider = self.create_slider(0.1, 2.0, 0.3, 10)
        self.spark_size_min_spinbox = QDoubleSpinBox()
        self.spark_size_min_spinbox.setRange(0.1, 2.0)
        self.spark_size_min_spinbox.setDecimals(1)
        spark_layout.addWidget(self.spark_size_min_slider, row, 1)
        spark_layout.addWidget(self.spark_size_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_size_min_slider, self.spark_size_min_spinbox, 'spark_size_min')
        row += 1
        
        spark_layout.addWidget(QLabel("Spark Size Max:"), row, 0)
        self.spark_size_max_slider = self.create_slider(0.1, 2.0, 0.5, 10)
        self.spark_size_max_spinbox = QDoubleSpinBox()
        self.spark_size_max_spinbox.setRange(0.1, 2.0)
        self.spark_size_max_spinbox.setDecimals(1)
        spark_layout.addWidget(self.spark_size_max_slider, row, 1)
        spark_layout.addWidget(self.spark_size_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_size_max_slider, self.spark_size_max_spinbox, 'spark_size_max')
        row += 1
        
        # Spark opacity range
        spark_layout.addWidget(QLabel("Spark Opacity Min:"), row, 0)
        self.spark_opacity_min_slider = self.create_slider(0, 255, 150, 1)
        self.spark_opacity_min_spinbox = QSpinBox()
        self.spark_opacity_min_spinbox.setRange(0, 255)
        spark_layout.addWidget(self.spark_opacity_min_slider, row, 1)
        spark_layout.addWidget(self.spark_opacity_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_opacity_min_slider, self.spark_opacity_min_spinbox, 'spark_opacity_min')
        row += 1
        
        spark_layout.addWidget(QLabel("Spark Opacity Max:"), row, 0)
        self.spark_opacity_max_slider = self.create_slider(0, 255, 255, 1)
        self.spark_opacity_max_spinbox = QSpinBox()
        self.spark_opacity_max_spinbox.setRange(0, 255)
        spark_layout.addWidget(self.spark_opacity_max_slider, row, 1)
        spark_layout.addWidget(self.spark_opacity_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_opacity_max_slider, self.spark_opacity_max_spinbox, 'spark_opacity_max')
        row += 1
        
        # Spark life range
        spark_layout.addWidget(QLabel("Spark Life Min (s):"), row, 0)
        self.spark_life_min_slider = self.create_slider(0.1, 5.0, 0.5, 10)
        self.spark_life_min_spinbox = QDoubleSpinBox()
        self.spark_life_min_spinbox.setRange(0.1, 5.0)
        self.spark_life_min_spinbox.setDecimals(1)
        spark_layout.addWidget(self.spark_life_min_slider, row, 1)
        spark_layout.addWidget(self.spark_life_min_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_life_min_slider, self.spark_life_min_spinbox, 'spark_life_min')
        row += 1
        
        spark_layout.addWidget(QLabel("Spark Life Max (s):"), row, 0)
        self.spark_life_max_slider = self.create_slider(0.1, 5.0, 2.0, 10)
        self.spark_life_max_spinbox = QDoubleSpinBox()
        self.spark_life_max_spinbox.setRange(0.1, 5.0)
        self.spark_life_max_spinbox.setDecimals(1)
        spark_layout.addWidget(self.spark_life_max_slider, row, 1)
        spark_layout.addWidget(self.spark_life_max_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_life_max_slider, self.spark_life_max_spinbox, 'spark_life_max')
        row += 1
        
        # Spark count ratio
        spark_layout.addWidget(QLabel("Spark Count Ratio:"), row, 0)
        self.spark_count_slider = self.create_slider(0.0, 2.0, 0.8, 10)
        self.spark_count_spinbox = QDoubleSpinBox()
        self.spark_count_spinbox.setRange(0.0, 2.0)
        self.spark_count_spinbox.setDecimals(1)
        spark_layout.addWidget(self.spark_count_slider, row, 1)
        spark_layout.addWidget(self.spark_count_spinbox, row, 2)
        self.connect_slider_spinbox(self.spark_count_slider, self.spark_count_spinbox, 'spark_count_ratio')
        row += 1
        
        layout.addWidget(spark_group)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons at the bottom (outside scroll area)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.setObjectName("reset_button")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def create_slider(self, min_val, max_val, default_val, scale=1):
        """Create a slider with the given range and default value"""
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(int(min_val * scale))
        slider.setMaximum(int(max_val * scale))
        slider.setValue(int(default_val * scale))
        return slider
    
    def connect_slider_spinbox(self, slider, spinbox, param_name):
        """Connect a slider and spinbox to update each other and the particle config"""
        scale = slider.maximum() / spinbox.maximum() if spinbox.maximum() > 0 else 1
        
        def update_from_slider(value):
            spinbox.setValue(value / scale)
            self.update_particle_param(param_name, value / scale)
        
        def update_from_spinbox(value):
            slider.setValue(int(value * scale))
            self.update_particle_param(param_name, value)
        
        slider.valueChanged.connect(update_from_slider)
        spinbox.valueChanged.connect(update_from_spinbox)
    
    def update_particle_param(self, param_name, value):
        """Update a single particle parameter"""
        self.piano_roll.update_particle_config(**{param_name: value})
    
    def on_particles_enabled_changed(self, state):
        """Handle enable/disable of particle system"""
        # For now, we don't have a global enable/disable, but we can disable spawning
        # by setting spawn rate to a very high value or stopping particle updates
        enabled = state == Qt.CheckState.Checked.value
        if not enabled:
            # Clear existing particles
            self.piano_roll.particles.clear()
            self.piano_roll.spark_particles.clear()
    
    def on_spark_enabled_changed(self, state):
        """Handle enable/disable of spark particles"""
        enabled = state == Qt.CheckState.Checked.value
        self.update_particle_param('spark_enabled', enabled)
        if not enabled:
            # Clear existing spark particles
            self.piano_roll.spark_particles.clear()
    
    def on_gradient_enabled_changed(self, state):
        """Handle enable/disable of gradient coloring"""
        enabled = state == Qt.CheckState.Checked.value
        self.piano_roll.update_gradient_config(enabled=enabled)
    
    def on_note_labels_changed(self, state):
        """Handle enable/disable of note labels"""
        enabled = state == Qt.CheckState.Checked.value
        self.piano_roll.update_visual_config(show_note_labels=enabled)
    
    def pick_bottom_color(self):
        """Open color picker for bottom color"""
        current_color = self.bottom_color_display.getColor()
        new_color = getColor(current_color)
        if new_color:  # getColor returns None if cancelled
            self.bottom_color_display.setColor(new_color)
            self.on_gradient_color_changed()
    
    def pick_middle_color(self):
        """Open color picker for middle color"""
        current_color = self.middle_color_display.getColor()
        new_color = getColor(current_color)
        if new_color:  # getColor returns None if cancelled
            self.middle_color_display.setColor(new_color)
            self.on_gradient_color_changed()
    
    def pick_top_color(self):
        """Open color picker for top color"""
        current_color = self.top_color_display.getColor()
        new_color = getColor(current_color)
        if new_color:  # getColor returns None if cancelled
            self.top_color_display.setColor(new_color)
            self.on_gradient_color_changed()

    def on_gradient_color_changed(self):
        """Handle gradient color changes from color displays"""
        # Get current color values from color displays - now in top to bottom order
        top_color = self.top_color_display.getColor()
        middle_color = self.middle_color_display.getColor()
        bottom_color = self.bottom_color_display.getColor()
        
        # Update the gradient configuration - colors should be in top to bottom order
        colors = [top_color, middle_color, bottom_color]
        positions = [0.0, 0.5, 1.0]
        self.piano_roll.set_gradient_colors(colors, positions)
    
    def apply_gradient_preset(self, preset_name):
        """Apply a gradient color preset"""
        presets = {
            "fire": {
                "colors": [(255, 50, 50), (255, 150, 0), (255, 100, 150)],  # Red to Orange to Pink
                "positions": [0.0, 0.5, 1.0]
            },
            "ocean": {
                "colors": [(0, 100, 200), (0, 150, 255), (100, 200, 255)],  # Dark Blue to Blue to Light Blue
                "positions": [0.0, 0.5, 1.0]
            },
            "sunset": {
                "colors": [(150, 50, 100), (255, 120, 50), (255, 200, 100)],  # Purple to Orange to Yellow
                "positions": [0.0, 0.5, 1.0]
            },
            "forest": {
                "colors": [(0, 80, 0), (50, 150, 50), (100, 255, 100)],  # Dark Green to Green to Light Green
                "positions": [0.0, 0.5, 1.0]
            },
            "emerald": {
                "colors": [(0, 100, 80), (0, 200, 150), (100, 255, 200)],  # Dark Teal to Emerald to Light Teal
                "positions": [0.0, 0.5, 1.0]
            },
            "gold": {
                "colors": [(150, 100, 0), (255, 200, 50), (255, 255, 150)],  # Dark Gold to Gold to Light Yellow
                "positions": [0.0, 0.5, 1.0]
            },
            "citrus": {
                "colors": [(200, 150, 0), (255, 220, 0), (255, 255, 100)],  # Orange-Yellow to Yellow to Light Yellow
                "positions": [0.0, 0.5, 1.0]
            },
            "purple": {
                "colors": [(80, 0, 120), (150, 50, 200), (200, 100, 255)],  # Dark Purple to Purple to Light Purple
                "positions": [0.0, 0.5, 1.0]
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.piano_roll.set_gradient_colors(preset["colors"], preset["positions"])
            # Update UI to reflect the preset - now in top, middle, bottom order
            if len(preset["colors"]) >= 3:
                # Top color (first in the preset)
                self.top_color_display.setColor(preset["colors"][0])
                
                # Middle color (middle of available colors)
                mid_idx = len(preset["colors"]) // 2
                self.middle_color_display.setColor(preset["colors"][mid_idx])
                
                # Bottom color (last in the preset)
                self.bottom_color_display.setColor(preset["colors"][-1])
    
    def load_current_values(self):
        """Load current particle configuration values into the UI"""
        config = self.piano_roll.get_particle_config()
        
        # Load regular particle values
        self.spawn_rate_slider.setValue(int(config['spawn_rate'] * 1000))
        self.spawn_rate_spinbox.setValue(config['spawn_rate'])
        
        self.vel_x_min_slider.setValue(int(config['initial_velocity_x_min']))
        self.vel_x_min_spinbox.setValue(config['initial_velocity_x_min'])
        
        self.vel_x_max_slider.setValue(int(config['initial_velocity_x_max']))
        self.vel_x_max_spinbox.setValue(config['initial_velocity_x_max'])
        
        self.vel_y_min_slider.setValue(int(config['initial_velocity_y_min']))
        self.vel_y_min_spinbox.setValue(config['initial_velocity_y_min'])
        
        self.vel_y_max_slider.setValue(int(config['initial_velocity_y_max']))
        self.vel_y_max_spinbox.setValue(config['initial_velocity_y_max'])
        
        self.size_min_slider.setValue(int(config['initial_size_min'] * 10))
        self.size_min_spinbox.setValue(config['initial_size_min'])
        
        self.size_max_slider.setValue(int(config['initial_size_max'] * 10))
        self.size_max_spinbox.setValue(config['initial_size_max'])
        
        self.opacity_min_slider.setValue(config['initial_opacity_min'])
        self.opacity_min_spinbox.setValue(config['initial_opacity_min'])
        
        self.opacity_max_slider.setValue(config['initial_opacity_max'])
        self.opacity_max_spinbox.setValue(config['initial_opacity_max'])
        
        self.life_min_slider.setValue(int(config['life_min'] * 10))
        self.life_min_spinbox.setValue(config['life_min'])
        
        self.life_max_slider.setValue(int(config['life_max'] * 10))
        self.life_max_spinbox.setValue(config['life_max'])
        
        self.turbulence_slider.setValue(int(config['turbulence_strength'] * 10))
        self.turbulence_spinbox.setValue(config['turbulence_strength'])
        
        self.damping_slider.setValue(int(config['damping_factor'] * 1000))
        self.damping_spinbox.setValue(config['damping_factor'])
        
        # Load spark particle values
        self.spark_enabled_cb.setChecked(config['spark_enabled'])
        
        self.spark_size_min_slider.setValue(int(config['spark_size_min'] * 10))
        self.spark_size_min_spinbox.setValue(config['spark_size_min'])
        
        self.spark_size_max_slider.setValue(int(config['spark_size_max'] * 10))
        self.spark_size_max_spinbox.setValue(config['spark_size_max'])
        
        self.spark_opacity_min_slider.setValue(config['spark_opacity_min'])
        self.spark_opacity_min_spinbox.setValue(config['spark_opacity_min'])
        
        self.spark_opacity_max_slider.setValue(config['spark_opacity_max'])
        self.spark_opacity_max_spinbox.setValue(config['spark_opacity_max'])
        
        self.spark_life_min_slider.setValue(int(config['spark_life_min'] * 10))
        self.spark_life_min_spinbox.setValue(config['spark_life_min'])
        
        self.spark_life_max_slider.setValue(int(config['spark_life_max'] * 10))
        self.spark_life_max_spinbox.setValue(config['spark_life_max'])
        
        self.spark_count_slider.setValue(int(config['spark_count_ratio'] * 10))
        self.spark_count_spinbox.setValue(config['spark_count_ratio'])
        
        # Enable particles checkbox (always enabled for now)
        self.particles_enabled_cb.setChecked(True)
        
        # Load gradient configuration values
        gradient_config = self.piano_roll.get_gradient_config()
        self.gradient_enabled_cb.setChecked(gradient_config['enabled'])
        
        # Load current gradient colors - now in top, middle, bottom order
        colors = gradient_config['colors']
        if len(colors) >= 3:
            # Set color displays to current gradient colors in the new order
            self.top_color_display.setColor(colors[0])      # First color = top
            self.middle_color_display.setColor(colors[1])   # Second color = middle  
            self.bottom_color_display.setColor(colors[2])   # Third color = bottom
        
        # Load visual configuration values
        visual_config = self.piano_roll.get_visual_config()
        self.show_note_labels_cb.setChecked(visual_config.get('show_note_labels', True))
    
    def reset_to_defaults(self):
        """Reset all particle parameters to their default values"""
        # Default configuration (same as in piano_roll.py)
        defaults = {
            'spawn_rate': 0.01,
            'initial_velocity_x_min': -5.0,
            'initial_velocity_x_max': 5.0,
            'initial_velocity_y_min': -80.0,
            'initial_velocity_y_max': -30.0,
            'initial_size_min': 0.4,
            'initial_size_max': 0.8,
            'initial_opacity_min': 40,
            'initial_opacity_max': 80,
            'turbulence_strength': 0.8,
            'damping_factor': 0.995,
            'life_min': 0.5,
            'life_max': 3.0,
            'spawn_x_spread': 0.9,
            'particles_per_note_base': 2,
            'particles_per_velocity': 20,
            'max_particles_per_note': 15,
            'spark_enabled': True,
            'spark_size_min': 0.3,
            'spark_size_max': 0.5,
            'spark_opacity_min': 150,
            'spark_opacity_max': 255,
            'spark_life_min': 0.5,
            'spark_life_max': 2.0,
            'spark_count_ratio': 0.8,
        }
        
        # Apply defaults to piano roll
        self.piano_roll.update_particle_config(**defaults)
        
        # Reset visual config to defaults
        self.piano_roll.update_visual_config(show_note_labels=True)
        
        # Update UI to reflect defaults
        self.load_current_values()
