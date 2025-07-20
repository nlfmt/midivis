import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk

def list_audio_devices():
    devices = sd.query_devices()
    return [device['name'] for device in devices if device['max_input_channels'] > 0]

def audio_callback(indata, outdata, frames, time, status):
    if status:
        print(status)
    outdata[:] = indata  # Simply pass the input audio to output

def start_stream():
    device_index = device_var.get()
    samplerate = 44100  # Standard audio sample rate
    channels = 1  # Mono audio
    
    global stream
    stream = sd.Stream(device=(device_index, None), samplerate=samplerate, channels=channels, dtype=np.float32, callback=audio_callback)
    stream.start()
    status_label.config(text="Streaming audio...")

def stop_stream():
    global stream
    if stream:
        stream.stop()
        stream.close()
        status_label.config(text="Audio stream stopped.")

# GUI Setup
root = tk.Tk()
root.title("Audio Input Playback")
root.geometry("800x600")  # Set window size

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

tk.Label(frame, text="Select Input Device:").pack()

available_devices = list_audio_devices()
device_var = tk.IntVar()

combo = ttk.Combobox(frame, values=available_devices)
combo.pack(fill=tk.BOTH, expand=True)
combo.current(0)

tk.Button(frame, text="Start Streaming", command=start_stream).pack(fill=tk.BOTH, expand=True)
tk.Button(frame, text="Stop Streaming", command=stop_stream).pack(fill=tk.BOTH, expand=True)

status_label = tk.Label(frame, text="")
status_label.pack()

if __name__ == "__main__":
    root.mainloop()
