import json
import os
import sys
from typing import Optional
from PySide6.QtCore import QObject, Signal


class SettingsManager(QObject):
    """Manages application settings persistence"""
    
    settings_changed = Signal()  # Emitted when settings are saved
    
    def __init__(self, settings_file: str = "settings.json"):
        super().__init__()
        self.settings_file = self._get_settings_path(settings_file)
        self._settings = {}
        self.load_settings()
    
    def _get_settings_path(self, filename: str) -> str:
        """Get the appropriate path for storing settings"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - use AppData
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA')
                if appdata:
                    settings_dir = os.path.join(appdata, 'AudioInputStreamer')
                else:
                    # Fallback to user home directory
                    settings_dir = os.path.join(os.path.expanduser('~'), '.AudioInputStreamer')
            else:
                # Linux/Mac
                settings_dir = os.path.join(os.path.expanduser('~'), '.AudioInputStreamer')
        else:
            # Running as script - use project directory for development
            settings_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Create directory if it doesn't exist
        os.makedirs(settings_dir, exist_ok=True)
        
        return os.path.join(settings_dir, filename)
    
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a setting value"""
        self._settings[key] = value
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            # Convert QByteArray to base64 string for JSON serialization
            settings_to_save = {}
            for key, value in self._settings.items():
                if hasattr(value, 'toBase64'):  # QByteArray
                    settings_to_save[key] = value.toBase64().data().decode('utf-8')
                else:
                    settings_to_save[key] = value
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            self.settings_changed.emit()
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Convert base64 strings back to QByteArray for geometry
                from PySide6.QtCore import QByteArray
                for key, value in loaded_settings.items():
                    if key == "window_geometry" and isinstance(value, str):
                        try:
                            self._settings[key] = QByteArray.fromBase64(value.encode('utf-8'))
                        except:
                            self._settings[key] = None
                    else:
                        self._settings[key] = value
                return True
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        # Initialize with defaults if file doesn't exist or loading failed
        self._settings = {
            "device_name": "",
            "window_geometry": None,
            "theme": "dark"
        }
        return False
    
    # Device settings methods
    def get_last_input_device(self) -> Optional[str]:
        """Get the last used input device name"""
        return self.get_setting('last_input_device')
    
    def set_last_input_device(self, device_name: str):
        """Set the last used input device name"""
        self.set_setting('last_input_device', device_name)
    
    def get_last_output_device(self) -> Optional[str]:
        """Get the last used output device name"""
        return self.get_setting('last_output_device')
    
    def set_last_output_device(self, device_name: str):
        """Set the last used output device name"""
        self.set_setting('last_output_device', device_name)
    
    def get_last_midi_device(self) -> Optional[str]:
        """Get the last used MIDI device name"""
        return self.get_setting('last_midi_device')
    
    def set_last_midi_device(self, device_name: str):
        """Set the last used MIDI device name"""
        self.set_setting('last_midi_device', device_name)
    
    # Backward compatibility
    def get_last_device(self) -> Optional[str]:
        """Get the last used device name (backward compatibility)"""
        return self.get_last_input_device()
    
    def set_last_device(self, device_name: str):
        """Set the last used device name (backward compatibility)"""
        self.set_last_input_device(device_name)
    
    def get_window_geometry(self):
        """Get saved window geometry"""
        return self.get_setting("window_geometry")
    
    def set_window_geometry(self, geometry):
        """Set window geometry"""
        self.set_setting("window_geometry", geometry)
    
    def get_theme(self) -> str:
        """Get current theme"""
        theme = self.get_setting("theme", "dark")
        return theme if isinstance(theme, str) else "dark"
    
    def set_theme(self, theme: str):
        """Set current theme"""
        self.set_setting("theme", theme)
    
    def get_show_piano_roll(self) -> bool:
        """Get whether to show piano roll view"""
        return self.get_setting('show_piano_roll', False)
    
    def set_show_piano_roll(self, show_piano_roll: bool):
        """Set whether to show piano roll view"""
        self.set_setting('show_piano_roll', show_piano_roll)
    
    def get_scroll_speed(self) -> int:
        """Get piano roll scroll speed"""
        return self.get_setting('scroll_speed', 100)
    
    def set_scroll_speed(self, speed: int):
        """Set piano roll scroll speed"""
        self.set_setting('scroll_speed', speed)
    
    def get_midi_delay(self) -> int:
        """Get MIDI delay compensation in milliseconds"""
        return self.get_setting('midi_delay', 0)
    
    def set_midi_delay(self, delay_ms: int):
        """Set MIDI delay compensation in milliseconds"""
        self.set_setting('midi_delay', delay_ms)
        
    def get_particle_config(self) -> dict:
        """Get particle system configuration"""
        return self.get_setting('particle_config', {})
    
    def set_particle_config(self, config: dict):
        """Set particle system configuration"""
        self.set_setting('particle_config', config)
        
    def get_gradient_config(self) -> dict:
        """Get gradient configuration for piano roll"""
        return self.get_setting('gradient_config', {})
    
    def set_gradient_config(self, config: dict):
        """Set gradient configuration for piano roll"""
        self.set_setting('gradient_config', config)
