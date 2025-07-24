"""
Piano keyboard layout utilities for realistic key positioning and sizing.

This module provides utilities for calculating the positions and sizes of piano keys
in a way that matches real piano keyboards, where the 88 keys are divided into
52 white keys with black keys overlaid between them.
"""

from typing import Tuple, NamedTuple

class KeyInfo(NamedTuple):
    """Information about a piano key's position and appearance."""
    x: float          # X position (left edge)
    width: float      # Width of the key
    is_black: bool    # Whether this is a black key
    z_order: int      # Drawing order (0=white keys, 1=black keys)

class PianoLayout:
    """Calculates realistic piano key positions and sizes."""
    
    # Standard 88-key piano starts at A0 (MIDI note 21) and ends at C8 (MIDI note 108)
    LOWEST_NOTE = 21
    HIGHEST_NOTE = 108
    NUM_KEYS = 88
    
    # Black key ratio relative to white key width
    BLACK_KEY_WIDTH_RATIO = 0.6
    BLACK_KEY_HEIGHT_RATIO = 0.65  # Black keys are typically shorter
    
    # Pattern of black keys in an octave (relative to C)
    # True = black key exists between this white key and the next
    BLACK_KEY_PATTERN = [True, False, True, False, False, True, False, True, False, True, False, False]
    # This represents: C-C#, D-D#, E (no black), F-F#, G-G#, A-A#, B (no black)
    
    @classmethod
    def midi_note_to_key_index(cls, midi_note: int) -> int:
        """Convert MIDI note to key index (0-87)."""
        return max(0, min(87, midi_note - cls.LOWEST_NOTE))
    
    @classmethod
    def key_index_to_midi_note(cls, key_index: int) -> int:
        """Convert key index to MIDI note."""
        return key_index + cls.LOWEST_NOTE
    
    @classmethod
    def is_black_key(cls, midi_note: int) -> bool:
        """Check if a MIDI note corresponds to a black key."""
        note_in_octave = midi_note % 12
        return note_in_octave in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
    
    @classmethod
    def is_white_key(cls, midi_note: int) -> bool:
        """Check if a MIDI note corresponds to a white key."""
        return not cls.is_black_key(midi_note)
    
    @classmethod
    def get_white_key_count(cls) -> int:
        """Get the total number of white keys (52 for 88-key piano)."""
        count = 0
        for i in range(cls.NUM_KEYS):
            midi_note = cls.key_index_to_midi_note(i)
            if cls.is_white_key(midi_note):
                count += 1
        return count
    
    @classmethod
    def get_white_key_index(cls, midi_note: int) -> int:
        """Get the index of a white key among all white keys (0-51)."""
        if cls.is_black_key(midi_note):
            raise ValueError(f"MIDI note {midi_note} is not a white key")
        
        white_key_index = 0
        for i in range(cls.NUM_KEYS):
            current_midi = cls.key_index_to_midi_note(i)
            if current_midi == midi_note:
                return white_key_index
            if cls.is_white_key(current_midi):
                white_key_index += 1
        
        raise ValueError(f"MIDI note {midi_note} not found in range")
    
    @classmethod
    def calculate_key_info(cls, midi_note: int, total_width: float) -> KeyInfo:
        """
        Calculate position and size information for a piano key.
        
        Args:
            midi_note: MIDI note number (21-108)
            total_width: Total width available for the entire keyboard
            
        Returns:
            KeyInfo with position, size, and appearance data
        """
        if not (cls.LOWEST_NOTE <= midi_note <= cls.HIGHEST_NOTE):
            raise ValueError(f"MIDI note {midi_note} is out of range {cls.LOWEST_NOTE}-{cls.HIGHEST_NOTE}")
        
        white_key_count = cls.get_white_key_count()  # 52 white keys
        white_key_width = total_width / white_key_count
        black_key_width = white_key_width * cls.BLACK_KEY_WIDTH_RATIO
        
        if cls.is_white_key(midi_note):
            # White key positioning
            white_key_index = cls.get_white_key_index(midi_note)
            x = white_key_index * white_key_width
            return KeyInfo(
                x=x,
                width=white_key_width,
                is_black=False,
                z_order=0
            )
        else:
            # Black key positioning - positioned between white keys
            # Find the white key to the left of this black key
            note_in_octave = midi_note % 12
            
            # Map black key positions relative to white keys
            # C# is between C and D, D# is between D and E, etc.
            if note_in_octave == 1:  # C#
                left_white_midi = midi_note - 1  # C
            elif note_in_octave == 3:  # D#
                left_white_midi = midi_note - 1  # D
            elif note_in_octave == 6:  # F#
                left_white_midi = midi_note - 1  # F
            elif note_in_octave == 8:  # G#
                left_white_midi = midi_note - 1  # G
            elif note_in_octave == 10:  # A#
                left_white_midi = midi_note - 1  # A
            else:
                raise ValueError(f"Invalid black key MIDI note: {midi_note}")
            
            # Get position of the left white key
            left_white_index = cls.get_white_key_index(left_white_midi)
            left_white_x = left_white_index * white_key_width
            
            # Position black key to overlap the right side of the left white key
            # and the left side of the right white key
            black_key_offset = white_key_width - (black_key_width / 2)
            x = left_white_x + black_key_offset
            
            return KeyInfo(
                x=x,
                width=black_key_width,
                is_black=True,
                z_order=1
            )
    
    @classmethod
    def get_all_key_info(cls, total_width: float) -> list[KeyInfo]:
        """
        Get position and size information for all 88 piano keys.
        
        Args:
            total_width: Total width available for the entire keyboard
            
        Returns:
            List of KeyInfo objects, one for each key in order from lowest to highest
        """
        key_info_list = []
        for i in range(cls.NUM_KEYS):
            midi_note = cls.key_index_to_midi_note(i)
            key_info = cls.calculate_key_info(midi_note, total_width)
            key_info_list.append(key_info)
        return key_info_list
    
    @classmethod
    def get_key_center_x(cls, midi_note: int, total_width: float) -> float:
        """Get the center X coordinate of a key."""
        key_info = cls.calculate_key_info(midi_note, total_width)
        return key_info.x + (key_info.width / 2)
