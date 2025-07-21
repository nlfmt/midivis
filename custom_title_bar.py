"""
Custom title bar widget for the Audio Streamer application
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSizeGrip, QFrame
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QCursor


class ResizeGrip(QWidget):
    """A resize grip widget for window edges and corners"""
    
    def __init__(self, parent, position):
        super().__init__(parent)
        self.parent_window = parent
        self.position = position
        self.mouse_pressed = False
        self.start_pos = QPoint()
        self.start_geometry = QRect()
        
        # Set cursor based on position
        if position == Qt.TopEdge or position == Qt.BottomEdge:
            self.setCursor(Qt.SizeVerCursor)
        elif position == Qt.LeftEdge or position == Qt.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
        elif position in ["top_left", "bottom_right"]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif position in ["top_right", "bottom_left"]:
            self.setCursor(Qt.SizeBDiagCursor)
        
        # Make widget transparent
        self.setStyleSheet("background: transparent;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.start_pos = event.globalPosition().toPoint()
            self.start_geometry = self.parent_window.geometry()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if not self.mouse_pressed:
            return
            
        global_pos = event.globalPosition().toPoint()
        delta = global_pos - self.start_pos
        
        # Get current geometry
        new_geometry = QRect(self.start_geometry)
        
        # Calculate new geometry based on position
        if self.position == Qt.TopEdge:
            new_geometry.setTop(self.start_geometry.top() + delta.y())
        elif self.position == Qt.BottomEdge:
            new_geometry.setBottom(self.start_geometry.bottom() + delta.y())
        elif self.position == Qt.LeftEdge:
            new_geometry.setLeft(self.start_geometry.left() + delta.x())
        elif self.position == Qt.RightEdge:
            new_geometry.setRight(self.start_geometry.right() + delta.x())
        elif self.position == "top_left":
            new_geometry.setTopLeft(self.start_geometry.topLeft() + delta)
        elif self.position == "top_right":
            new_geometry.setTopRight(self.start_geometry.topRight() + delta)
        elif self.position == "bottom_left":
            new_geometry.setBottomLeft(self.start_geometry.bottomLeft() + delta)
        elif self.position == "bottom_right":
            new_geometry.setBottomRight(self.start_geometry.bottomRight() + delta)
        
        # Enforce minimum size
        min_width = self.parent_window.minimumWidth()
        min_height = self.parent_window.minimumHeight()
        
        if new_geometry.width() < min_width:
            if self.position in [Qt.LeftEdge, "top_left", "bottom_left"]:
                new_geometry.setLeft(new_geometry.right() - min_width)
            else:
                new_geometry.setRight(new_geometry.left() + min_width)
                
        if new_geometry.height() < min_height:
            if self.position in [Qt.TopEdge, "top_left", "top_right"]:
                new_geometry.setTop(new_geometry.bottom() - min_height)
            else:
                new_geometry.setBottom(new_geometry.top() + min_height)
        
        # Apply the new geometry
        self.parent_window.setGeometry(new_geometry)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        event.accept()


class CustomGrip(QWidget):
    """Simple custom grip for resizing frameless window"""
    
    def __init__(self, parent, position, disable_color=False):
        super().__init__(parent)
        self.parent_window = parent
        self.position = position
        
        # Create the actual resize grip
        self.resize_grip = ResizeGrip(parent, position)
        
        # Set up geometry based on position
        self.update_geometry()
        
    def update_geometry(self):
        """Update grip geometry based on parent size"""
        parent_rect = self.parent_window.rect()
        
        if self.position == Qt.TopEdge:
            self.setGeometry(0, 0, parent_rect.width(), 10)
            self.resize_grip.setGeometry(0, 0, parent_rect.width(), 10)
        elif self.position == Qt.BottomEdge:
            self.setGeometry(0, parent_rect.height() - 10, parent_rect.width(), 10)
            self.resize_grip.setGeometry(0, parent_rect.height() - 10, parent_rect.width(), 10)
        elif self.position == Qt.LeftEdge:
            self.setGeometry(0, 10, 10, parent_rect.height() - 20)
            self.resize_grip.setGeometry(0, 10, 10, parent_rect.height() - 20)
        elif self.position == Qt.RightEdge:
            self.setGeometry(parent_rect.width() - 10, 10, 10, parent_rect.height() - 20)
            self.resize_grip.setGeometry(parent_rect.width() - 10, 10, 10, parent_rect.height() - 20)




class CustomTitleBar(QWidget):
    """Custom draggable title bar widget"""
    
    # Signals for window control
    close_clicked = Signal()
    minimize_clicked = Signal()
    
    def __init__(self, title="Audio Input Streamer", parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.title = title
        self.drag_position = QPoint()
        
        self.setup_ui()
        self.setup_style()
        
        # Enable dragging
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
    def setup_ui(self):
        """Setup the title bar UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 0, 0)  # Remove vertical margins to eliminate gaps
        layout.setSpacing(0)  # No spacing between buttons
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))  # Reduced font size
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); padding: 2px 0px;")  # 70% transparency
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically
        layout.addWidget(self.title_label)
        
        # Spacer
        layout.addStretch()
        
        # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(40, 35)  # Match title bar height
        self.minimize_btn.setObjectName("title_button")
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(40, 35)  # Match title bar height
        self.close_btn.setObjectName("close_button")
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.setFixedHeight(35)  # Match button height to eliminate gaps
    
    def setup_style(self):
        """Setup the title bar styling - styles are now in main theme"""
        pass  # Styles are now handled in theme.py
    
    def set_title(self, title):
        """Update the title text"""
        self.title = title
        self.title_label.setText(title)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.parent_window:
            # Simple title bar dragging - no resize interference
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        # Handle dragging
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            not self.drag_position.isNull() and 
            self.parent_window):
            
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = QPoint()
        event.accept()



