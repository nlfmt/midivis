import sounddevice as sd
import numpy as np
from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal
import json
import os


class AudioDevice:
    """Represents an audio device with its properties"""
    def __init__(self, index: int, name: str, channels: int, sample_rate: float):
        self.index = index
        self.name = name
        self.channels = channels
        self.sample_rate = sample_rate
    
    def __repr__(self):
        return f"AudioDevice(index={self.index}, name='{self.name}', channels={self.channels})"


class AudioManager(QObject):
    """Manages audio streaming functionality"""
    
    # Signals for UI updates
    status_changed = Signal(str, str)  # message, color
    streaming_started = Signal(str)    # device_name
    streaming_stopped = Signal()
    error_occurred = Signal(str)       # error_message
    
    def __init__(self):
        super().__init__()
        self.stream = None
        self.is_muted = False
        self.current_device: Optional[AudioDevice] = None
        self.available_devices: List[AudioDevice] = []
        self.refresh_devices()
    
    def refresh_devices(self) -> List[AudioDevice]:
        """Refresh and return list of available input devices"""
        self.available_devices.clear()
        
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    audio_device = AudioDevice(
                        index=i,
                        name=device['name'],
                        channels=device['max_input_channels'],
                        sample_rate=device.get('default_samplerate', 44100)
                    )
                    self.available_devices.append(audio_device)
        except Exception as e:
            self.error_occurred.emit(f"Failed to query devices: {str(e)}")
        
        return self.available_devices
    
    def get_device_by_name(self, name: str) -> Optional[AudioDevice]:
        """Find device by name"""
        return next((device for device in self.available_devices if device.name == name), None)
    
    def audio_callback(self, indata, outdata, frames, time, status):
        """Audio stream callback function"""
        if status:
            print(f"Audio callback status: {status}")
        
        if self.is_muted:
            outdata[:] = 0  # Output silence when muted
        else:
            outdata[:] = indata  # Pass input to output
    
    def start_streaming(self, device: AudioDevice) -> bool:
        """Start audio streaming with the specified device"""
        try:
            self.stop_streaming()
            
            channels = min(device.channels, 2)  # Use stereo if available, otherwise mono
            
            self.stream = sd.Stream(
                device=(device.index, None),
                samplerate=device.sample_rate,
                channels=channels,
                dtype=np.float32,
                callback=self.audio_callback
            )
            
            self.stream.start()
            self.current_device = device
            
            self.streaming_started.emit(device.name)
            self.status_changed.emit(f"Streaming: {device.name}", "#00cc00")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start streaming: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.status_changed.emit(error_msg, "#ff4444")
            return False
    
    def stop_streaming(self):
        """Stop current audio streaming"""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                self.current_device = None
                
                self.streaming_stopped.emit()
                self.status_changed.emit("Stream stopped", "#888888")
            except Exception as e:
                print(f"Error stopping stream: {e}")
    
    def toggle_mute(self) -> bool:
        """Toggle mute state and return new state"""
        self.is_muted = not self.is_muted
        return self.is_muted
    
    def is_streaming(self) -> bool:
        """Check if currently streaming"""
        return self.stream is not None and self.stream.active
    
    def get_current_device_name(self) -> str:
        """Get name of currently selected device"""
        return self.current_device.name if self.current_device else ""
