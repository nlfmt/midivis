from typing import List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer, QMetaObject, Qt
import time

# Defer heavy imports until needed
_rtmidi = None

def _get_rtmidi():
    """Lazy import of rtmidi"""
    global _rtmidi
    if _rtmidi is None:
        try:
            import rtmidi
            _rtmidi = rtmidi
        except ImportError:
            print("python-rtmidi not installed. Install with: pip install python-rtmidi")
            raise
    return _rtmidi


class MIDIDevice:
    """Represents a MIDI input device"""
    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name
    
    def __repr__(self):
        return f"MIDIDevice(index={self.index}, name='{self.name}')"


class MIDIManager(QObject):
    """Manages MIDI input functionality"""
    
    # Signals for UI updates
    note_on = Signal(int, int)   # note_number, velocity
    note_off = Signal(int)       # note_number
    error_occurred = Signal(str) # error_message
    
    # Internal signals for delayed processing (connect to main thread)
    _delayed_note_on_signal = Signal(int, int, int)   # note, velocity, delay_ms
    _delayed_note_off_signal = Signal(int, int)       # note, delay_ms
    
    def __init__(self):
        super().__init__()
        self.midi_in = None
        self.current_device: Optional[MIDIDevice] = None
        self.available_devices: List[MIDIDevice] = []
        self.delay_ms = 0  # MIDI delay compensation in milliseconds
        
        # Connect internal signals to delayed handlers
        self._delayed_note_on_signal.connect(self._handle_delayed_note_on)
        self._delayed_note_off_signal.connect(self._handle_delayed_note_off)
        
    def refresh_devices(self) -> List[MIDIDevice]:
        """Refresh and return list of available MIDI input devices"""
        self.available_devices.clear()
        
        try:
            rtmidi = _get_rtmidi()
            midi_in = rtmidi.MidiIn()
            
            # Get available ports
            ports = midi_in.get_ports()
            
            for i, port_name in enumerate(ports):
                device = MIDIDevice(index=i, name=port_name.strip())
                self.available_devices.append(device)
            
            midi_in.close_port()
            del midi_in
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to query MIDI devices: {str(e)}")
        
        return self.available_devices
    
    def set_delay(self, delay_ms: int):
        """Set MIDI delay compensation in milliseconds"""
        self.delay_ms = max(0, delay_ms)  # Ensure non-negative delay
    
    def get_device_by_name(self, name: str) -> Optional[MIDIDevice]:
        """Find MIDI device by name"""
        return next((device for device in self.available_devices if device.name == name), None)
    
    def start_listening(self, device: MIDIDevice) -> bool:
        """Start listening to MIDI input from the specified device"""
        try:
            self.stop_listening()
            
            rtmidi = _get_rtmidi()
            self.midi_in = rtmidi.MidiIn()
            
            # Check if the device index is still valid
            available_ports = self.midi_in.get_ports()
            if device.index >= len(available_ports):
                error_msg = f"MIDI device index {device.index} is no longer valid"
                self.error_occurred.emit(error_msg)
                return False
            
            # Set callback for MIDI messages
            self.midi_in.set_callback(self._midi_callback)
            
            # Open the specified port
            self.midi_in.open_port(device.index)
            
            self.current_device = device
            return True
            
        except Exception as e:
            error_msg = f"Failed to start MIDI listening: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def stop_listening(self):
        """Stop MIDI input listening"""
        if self.midi_in:
            try:
                self.midi_in.close_port()
                self.midi_in = None
                self.current_device = None
            except Exception as e:
                print(f"Error stopping MIDI listening: {e}")
    
    def _midi_callback(self, event, data=None):
        """Handle incoming MIDI messages"""
        message, deltatime = event
        
        if len(message) >= 2:
            status = message[0]
            
            # Note On (0x90-0x9F)
            if status >= 0x90 and status <= 0x9F:
                note = message[1]
                velocity = message[2] if len(message) > 2 else 64
                
                if velocity > 0:
                    if self.delay_ms > 0:
                        # Schedule delayed emission using internal signal
                        self._delayed_note_on_signal.emit(note, velocity, self.delay_ms)
                    else:
                        # Emit immediately (signals are thread-safe in Qt)
                        self.note_on.emit(note, velocity)
                else:
                    # Note on with velocity 0 is equivalent to note off
                    if self.delay_ms > 0:
                        self._delayed_note_off_signal.emit(note, self.delay_ms)
                    else:
                        self.note_off.emit(note)
            
            # Note Off (0x80-0x8F)
            elif status >= 0x80 and status <= 0x8F:
                note = message[1]
                if self.delay_ms > 0:
                    self._delayed_note_off_signal.emit(note, self.delay_ms)
                else:
                    self.note_off.emit(note)
    
    # Helper methods for thread-safe MIDI event handling
    def _handle_delayed_note_on(self, note: int, velocity: int, delay_ms: int):
        """Handle delayed note_on signal using QTimer"""
        QTimer.singleShot(delay_ms, lambda: self.note_on.emit(note, velocity))
    
    def _handle_delayed_note_off(self, note: int, delay_ms: int):
        """Handle delayed note_off signal using QTimer"""
        QTimer.singleShot(delay_ms, lambda: self.note_off.emit(note))
    
    def is_listening(self) -> bool:
        """Check if currently listening to MIDI"""
        return self.midi_in is not None
    
    def get_current_device_name(self) -> str:
        """Get name of currently selected MIDI device"""
        return self.current_device.name if self.current_device else ""
    
    def test_device(self, device: MIDIDevice) -> bool:
        """Test if a MIDI device can be opened without starting listening"""
        try:
            rtmidi = _get_rtmidi()
            test_midi_in = rtmidi.MidiIn()
            
            # Check if the device index is valid
            available_ports = test_midi_in.get_ports()
            if device.index >= len(available_ports):
                test_midi_in.close_port()
                del test_midi_in
                return False
            
            # Try to open and immediately close
            test_midi_in.open_port(device.index)
            test_midi_in.close_port()
            del test_midi_in
            return True
            
        except Exception as e:
            print(f"MIDI device test failed for {device.name}: {e}")
            return False
    
    def start_demo_mode(self):
        """Start demo mode that plays a sequence of notes to demonstrate the piano roll"""
        # Define a simple melody sequence (note, velocity, duration_ms, pause_after_ms)
        demo_sequence = [
            # C major scale up
            (60, 80, 300, 100),   # C4
            (62, 75, 300, 100),   # D4
            (64, 85, 300, 100),   # E4
            (65, 70, 300, 100),   # F4
            (67, 90, 300, 100),   # G4
            (69, 75, 300, 100),   # A4
            (71, 80, 300, 100),   # B4
            (72, 95, 500, 200),   # C5 (longer note)
            
            # Simple chord progression
            (60, 70, 800, 50),    # C4 chord start
            (64, 70, 800, 50),    # E4
            (67, 70, 800, 300),   # G4
            
            (65, 75, 800, 50),    # F4 chord
            (69, 75, 800, 50),    # A4
            (72, 75, 800, 300),   # C5
            
            (62, 80, 800, 50),    # D4 chord
            (66, 80, 800, 50),    # F#4
            (69, 80, 800, 300),   # A4
            
            (67, 85, 1000, 50),   # G4 final chord
            (71, 85, 1000, 50),   # B4
            (74, 85, 1000, 500),  # D5
        ]
        
        self._play_demo_sequence(demo_sequence, 0)
    
    def _play_demo_sequence(self, sequence, index):
        """Recursively play demo sequence notes"""
        if index >= len(sequence):
            return  # Demo finished
        
        note, velocity, duration_ms, pause_after_ms = sequence[index]
        
        # Play note on
        self.note_on.emit(note, velocity)
        
        # Schedule note off
        QTimer.singleShot(duration_ms, lambda: self.note_off.emit(note))
        
        # Schedule next note
        next_delay = duration_ms + pause_after_ms
        QTimer.singleShot(next_delay, lambda: self._play_demo_sequence(sequence, index + 1))
