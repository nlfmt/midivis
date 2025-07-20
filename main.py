import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk
from functools import partial
import json
import os

class AudioStreamer:
    def __init__(self, root):
        self.root = root
        self.stream = None
        self.is_muted = False
        self.current_device_index = 0
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        # Setup UI
        self.setup_ui()
        
        # Load previous device and start streaming
        self.load_settings()
        self.root.after(100, self.start_stream)
    
    def setup_ui(self):
        # Configure the root window
        self.root.title("Audio Input Playback")
        self.root.geometry("350x180")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")
        
        # Create a main frame with padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style configuration
        style = ttk.Style()
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TCombobox', font=('Segoe UI', 10))
        style.configure('TFrame', background="#f0f0f0")
        
        # Device selection section
        ttk.Label(main_frame, text="Select Input Device:").pack(anchor=tk.W, pady=(0, 5))
        
        # Get available devices
        self.device_list = self.get_input_devices()
        self.available_devices = [device['name'] for device in self.device_list]
        
        # Device dropdown
        self.device_var = tk.StringVar()
        self.combo = ttk.Combobox(main_frame, textvariable=self.device_var, values=self.available_devices, width=40)
        self.combo.pack(fill=tk.X, pady=(0, 15))
        self.combo.current(0)
        self.combo.bind("<<ComboboxSelected>>", self.on_device_changed)
        
        # Control buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mute button with icon-like text
        self.mute_button = ttk.Button(buttons_frame, text="🔊 Unmuted", command=self.toggle_mute, width=15)
        self.mute_button.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Initializing...", foreground="#555555")
        self.status_label.pack(side=tk.LEFT)
        
        # Add a visual indicator for streaming status
        self.status_indicator = tk.Canvas(self.status_frame, width=10, height=10, bg="#f0f0f0", highlightthickness=0)
        self.status_indicator.pack(side=tk.RIGHT, padx=(5, 0))
        self.status_indicator.create_oval(2, 2, 8, 8, fill="gray", outline="")
    
    def get_input_devices(self):
        """Get complete device information for input devices"""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                # Store complete device info with index
                input_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'default_samplerate': device.get('default_samplerate', 44100)
                })
        
        return input_devices
    
    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
        
        if self.is_muted:
            outdata[:] = 0  # Output silence when muted
        else:
            outdata[:] = indata  # Pass the input audio to output
    
    def start_stream(self):
        try:
            # Stop any existing stream
            self.stop_stream(update_ui=False)
            
            # Get the device index from the combobox
            selected_name = self.device_var.get()
            device_info = next((device for device in self.device_list if device['name'] == selected_name), None)
            
            if not device_info:
                self.update_status(f"Device not found. Using default.", "orange")
                # Find first available device as fallback
                if self.device_list:
                    device_info = self.device_list[0]
                    self.device_var.set(device_info['name'])
                    self.combo.current(0)
                else:
                    self.update_status("No input devices available", "red")
                    self.status_indicator.itemconfig(1, fill="red")
                    return
            
            device_index = device_info['index']
            samplerate = device_info['default_samplerate']
            channels = min(device_info['channels'], 2)  # Use stereo if available, otherwise mono
            
            # Start the new stream
            self.stream = sd.Stream(
                device=(device_index, None), 
                samplerate=samplerate, 
                channels=channels, 
                dtype=np.float32, 
                callback=self.audio_callback
            )
            self.stream.start()
            
            # Save the current device
            self.save_settings()
            
            # Update UI
            self.update_status(f"Streaming: {selected_name}", "#007700")
            self.status_indicator.itemconfig(1, fill="#00cc00")  # Green indicator
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
            self.status_indicator.itemconfig(1, fill="red")
    
    def stop_stream(self, update_ui=True):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                
                if update_ui:
                    self.update_status("Stream stopped", "gray")
                    self.status_indicator.itemconfig(1, fill="gray")
            except:
                pass
    
    def on_device_changed(self, event):
        # Restart stream with the new device
        self.start_stream()
    
    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_button.config(text="🔇 Muted")
        else:
            self.mute_button.config(text="🔊 Unmuted")
    
    def update_status(self, message, color):
        self.status_label.config(text=message, foreground=color)
    
    def save_settings(self):
        """Save current device selection to settings file"""
        try:
            settings = {
                "device_name": self.device_var.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def load_settings(self):
        """Load previous device selection from settings file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                saved_device = settings.get("device_name")
                if saved_device:
                    # Check if the saved device still exists
                    if saved_device in self.available_devices:
                        self.device_var.set(saved_device)
                        self.combo.current(self.available_devices.index(saved_device))
                    else:
                        # Device no longer exists, use fallback with notification
                        self.update_status(f"Saved device not found", "orange")
                        # Will use first available device (default behavior)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def on_closing(self):
        self.stop_stream()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioStreamer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()