from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal
import json
import os

# Defer heavy imports until needed
_sounddevice = None
_numpy = None

def _get_sounddevice():
    """Lazy import of sounddevice"""
    global _sounddevice
    if _sounddevice is None:
        import sounddevice as sd
        _sounddevice = sd
    return _sounddevice

def _get_numpy():
    """Lazy import of numpy"""
    global _numpy
    if _numpy is None:
        import numpy as np
        _numpy = np
    return _numpy


class AudioDevice:
    """Represents an audio device with its properties"""
    def __init__(self, index: int, name: str, channels: int, sample_rate: float, hostapi: int, hostapi_name: str, device_type: str = "input"):
        self.index = index
        self.name = name
        self.channels = channels
        self.sample_rate = sample_rate
        self.hostapi = hostapi
        self.hostapi_name = hostapi_name
        self.device_type = device_type  # "input" or "output"
    
    def __repr__(self):
        return f"AudioDevice(index={self.index}, name='{self.name}', channels={self.channels}, api={self.hostapi_name})"


class AudioManager(QObject):
    """Manages audio streaming functionality"""
    
    # Signals for UI updates
    status_changed = Signal(str, str)  # message, color
    streaming_started = Signal(str)    # device_name
    streaming_stopped = Signal()
    error_occurred = Signal(str)       # error_message
    audio_data_ready = Signal(object)  # numpy array of audio data for spectrum analysis
    
    def __init__(self, lazy_init=False):
        super().__init__()
        self.stream = None
        self.is_muted = False
        self.current_input_device: Optional[AudioDevice] = None
        self.current_output_device: Optional[AudioDevice] = None
        self.available_input_devices: List[AudioDevice] = []
        self.available_output_devices: List[AudioDevice] = []
        
        # Only refresh devices if not lazy initialization
        if not lazy_init:
            self.refresh_devices()
    
    def refresh_devices(self) -> tuple[List[AudioDevice], List[AudioDevice]]:
        """Refresh and return lists of available input and output devices"""
        self.available_input_devices.clear()
        self.available_output_devices.clear()
        
        try:
            sd = _get_sounddevice()
            devices = sd.query_devices()
            
            # Get host API information
            hostapis = []
            try:
                for i in range(len(devices)):
                    hostapi_index = devices[i].get('hostapi', 0)
                    if hostapi_index >= len(hostapis):
                        while len(hostapis) <= hostapi_index:
                            try:
                                hostapi_info = sd.query_hostapis(len(hostapis))
                                hostapis.append(hostapi_info)
                            except:
                                hostapis.append({'name': 'Unknown'})
            except:
                pass
            
            # Group devices by name to find the best version (non-truncated)
            input_device_groups = {}
            output_device_groups = {}
            
            for i, device in enumerate(devices):
                device_name = device.get('name', '').strip()
                hostapi_index = device.get('hostapi', 0)
                hostapi_name = hostapis[hostapi_index]['name'] if hostapi_index < len(hostapis) else 'Unknown'
                
                # Create device info
                device_info = {
                    'index': i,
                    'name': device_name,
                    'hostapi': hostapi_index,
                    'hostapi_name': hostapi_name,
                    'sample_rate': device.get('default_samplerate', 44100),
                    'name_length': len(device_name)
                }
                
                # Process input devices
                if device['max_input_channels'] > 0:
                    channels = device['max_input_channels']
                    device_info['channels'] = channels
                    
                    # Group by base name (for deduplication)
                    base_name = self._get_base_device_name(device_name)
                    
                    if base_name not in input_device_groups:
                        input_device_groups[base_name] = []
                    input_device_groups[base_name].append(device_info)
                
                # Process output devices (WDM-KS, WASAPI, and DirectSound for better compatibility)
                if device['max_output_channels'] > 0 and hostapi_name in ['Windows WDM-KS', 'Windows WASAPI', 'Windows DirectSound']:
                    channels = device['max_output_channels']
                    device_info['channels'] = channels
                    
                    # Group by base name (for deduplication)
                    base_name = self._get_base_device_name(device_name)
                    
                    if base_name not in output_device_groups:
                        output_device_groups[base_name] = []
                    output_device_groups[base_name].append(device_info)
            
            # Select best device from each group (longest name = least truncated)
            for base_name, device_list in input_device_groups.items():
                best_device = max(device_list, key=lambda d: (d['name_length'], d['hostapi'] != 0))  # Prefer longer names and non-MME
                
                audio_device = AudioDevice(
                    index=best_device['index'],
                    name=best_device['name'],
                    channels=best_device['channels'],
                    sample_rate=best_device['sample_rate'],
                    hostapi=best_device['hostapi'],
                    hostapi_name=best_device['hostapi_name'],
                    device_type="input"
                )
                self.available_input_devices.append(audio_device)
            
            for base_name, device_list in output_device_groups.items():
                best_device = max(device_list, key=lambda d: d['name_length'])  # WDM-KS names should be full
                
                audio_device = AudioDevice(
                    index=best_device['index'],
                    name=best_device['name'],
                    channels=best_device['channels'],
                    sample_rate=best_device['sample_rate'],
                    hostapi=best_device['hostapi'],
                    hostapi_name=best_device['hostapi_name'],
                    device_type="output"
                )
                self.available_output_devices.append(audio_device)
            
            # Sort devices by name for consistent ordering
            self.available_input_devices.sort(key=lambda d: d.name.lower())
            self.available_output_devices.sort(key=lambda d: d.name.lower())
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to query devices: {str(e)}")
        
        return self.available_input_devices, self.available_output_devices
    
    def _get_base_device_name(self, name: str) -> str:
        """Extract base device name for grouping similar devices"""
        # Remove common prefixes and suffixes that might vary between APIs
        base = name.lower().strip()
        
        # Remove common audio API artifacts
        prefixes_to_remove = ['microphone (', 'line in (', 'line out (', 'speakers (', 'headphones (']
        suffixes_to_remove = [' wave)', ' ks)', ' directsound)', ' mme)']
        
        for prefix in prefixes_to_remove:
            if base.startswith(prefix):
                base = base[len(prefix):]
                break
        
        for suffix in suffixes_to_remove:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        
        # Handle truncated names by using first part as base
        if len(name) == 31:  # MME truncation length
            # For truncated names, use everything before the last word as base
            parts = base.split()
            if len(parts) > 1:
                base = ' '.join(parts[:-1])
        
        return base
    
    def get_input_device_by_name(self, name: str) -> Optional[AudioDevice]:
        """Find input device by name"""
        return next((device for device in self.available_input_devices if device.name == name), None)
    
    def get_output_device_by_name(self, name: str) -> Optional[AudioDevice]:
        """Find output device by name"""
        return next((device for device in self.available_output_devices if device.name == name), None)
    
    def get_device_by_name(self, name: str) -> Optional[AudioDevice]:
        """Find device by name (backward compatibility - searches input devices)"""
        return self.get_input_device_by_name(name)
    
    def audio_callback(self, indata, outdata, frames, time, status):
        """Audio stream callback function"""
        # Emit audio data for spectrum analysis (always emit, even when muted)
        self.audio_data_ready.emit(indata.copy())
        
        if self.is_muted:
            outdata[:] = 0  # Output silence when muted
        else:
            outdata[:] = indata  # Pass input to output
    
    def start_streaming(self, input_device: AudioDevice, output_device: Optional[AudioDevice] = None) -> bool:
        """Start audio streaming with the specified input and output devices"""
        try:
            self.stop_streaming()
            
            sd = _get_sounddevice()
            np = _get_numpy()
            
            input_channels = min(input_device.channels, 2)  # Use stereo if available, otherwise mono
            
            # If no output device specified, use default
            if output_device:
                output_device_index = output_device.index
                output_channels = min(output_device.channels, 2)
                
                # For WDM-KS devices, try to match sample rates and use compatible settings
                if output_device.hostapi_name == 'Windows WDM-KS':
                    # WDM-KS devices are picky about sample rates and formats
                    # Try to use the output device's preferred sample rate
                    sample_rate = output_device.sample_rate
                    
                    # Ensure channel count compatibility
                    channels = min(input_channels, output_channels)
                else:
                    sample_rate = input_device.sample_rate
                    channels = input_channels
            else:
                output_device_index = None  # Use default output
                sample_rate = input_device.sample_rate
                channels = input_channels
            
            # Try to create the stream with error handling for device compatibility
            try:
                self.stream = sd.Stream(
                    device=(input_device.index, output_device_index),
                    samplerate=sample_rate,
                    channels=channels,
                    dtype=np.float32,
                    callback=self.audio_callback
                )
                
                self.stream.start()
                
            except Exception as stream_error:
                # If WDM-KS fails, try falling back to default output
                if output_device and output_device.hostapi_name == 'Windows WDM-KS':
                    self.stream = sd.Stream(
                        device=(input_device.index, None),  # Use default output
                        samplerate=input_device.sample_rate,
                        channels=input_channels,
                        dtype=np.float32,
                        callback=self.audio_callback
                    )
                    
                    self.stream.start()
                    output_device = None  # Mark as using default output
                else:
                    raise stream_error
            
            self.current_input_device = input_device
            self.current_output_device = output_device
            
            # Create status message
            if output_device:
                status_msg = f"Streaming: {input_device.name} → {output_device.name}"
            else:
                status_msg = f"Streaming: {input_device.name} → Default Output"
            
            self.streaming_started.emit(input_device.name)
            self.status_changed.emit(status_msg, "#00cc00")
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
                self.current_input_device = None
                self.current_output_device = None
                
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
        """Get name of currently selected input device"""
        return self.current_input_device.name if self.current_input_device else ""
    
    def get_current_input_device_name(self) -> str:
        """Get name of currently selected input device"""
        return self.current_input_device.name if self.current_input_device else ""
    
    def get_current_output_device_name(self) -> str:
        """Get name of currently selected output device"""
        return self.current_output_device.name if self.current_output_device else "Default Output"
