# Audio Input Streamer

A professional audio streaming application built with PySide6 that allows you to stream audio from any Windows audio device with real-time spectrum analysis and a modern dark theme.

## Project Structure

```
sound_listener/
├── src/                          # Source code
│   ├── main.py                   # Main application entry point
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── audio_manager.py      # Audio device management and streaming
│   │   └── settings_manager.py   # Settings persistence
│   └── ui/                       # User interface components
│       ├── __init__.py
│       ├── main_window.py        # Main application window
│       ├── custom_title_bar.py   # Custom frameless window and title bar
│       ├── spectrum_analyzer.py  # Real-time spectrum analyzer widget
│       └── theme.py              # Dark theme styling
├── assets/                       # Static assets
│   └── icons/                    # Application icons
│       ├── icon.svg              # Source SVG icon
│       ├── icon.png              # PNG version
│       └── icon.ico              # Windows ICO format
├── build/                        # Build configuration and scripts
│   ├── AudioInputStreamer.spec   # PyInstaller configuration
│   └── build.bat                 # Windows build script
├── docs/                         # Documentation
│   └── BUILD.md                  # Build instructions
├── main.py                       # Root launcher script
├── requirements.txt              # Python dependencies
└── settings.json                 # User settings (auto-generated)
```

## Features

- **Real-time Audio Streaming**: Stream from any Windows audio input device
- **High-Resolution Spectrum Analyzer**: 4096-point FFT with logarithmic frequency scaling
- **Modern Dark Theme**: Professional UI with custom title bar and rounded corners
- **Custom Window Controls**: Draggable title bar with minimize/close buttons
- **Settings Persistence**: Remembers last used device and window geometry
- **Mute Functionality**: Toggle audio streaming on/off
- **Professional Packaging**: Single executable build support

## Quick Start

### Running from Source

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

### Building Executable

1. **Convert icon** (if not done):
   - Convert `assets/icons/icon.svg` to `assets/icons/icon.ico`

2. **Build**:
   ```bash
   cd build
   build.bat
   ```

3. **Find executable**:
   - Located at `build/dist/AudioInputStreamer.exe`

## Development

### Code Organization

- **Core (`src/core/`)**: Business logic and data management
  - `audio_manager.py`: Handles audio device enumeration, streaming, and processing
  - `settings_manager.py`: Manages application settings and persistence

- **UI (`src/ui/`)**: User interface components
  - `main_window.py`: Main application window and layout
  - `custom_title_bar.py`: Custom frameless window with draggable title bar
  - `spectrum_analyzer.py`: Real-time spectrum visualization widget
  - `theme.py`: Dark theme CSS styling

- **Assets (`assets/`)**: Static resources
  - Icons in multiple formats for different use cases

- **Build (`build/`)**: Build configuration and scripts
  - PyInstaller spec file and build scripts

### Key Technologies

- **PySide6**: Modern Qt6 bindings for Python
- **NumPy/SciPy**: High-performance audio processing and FFT
- **SoundDevice**: Cross-platform audio I/O
- **PyInstaller**: Single executable packaging

### Architecture

The application follows a clean separation of concerns:

1. **Audio Pipeline**: `AudioManager` handles device enumeration, audio capture, and real-time processing
2. **UI Layer**: Qt-based interface with custom widgets and styling
3. **Settings Layer**: JSON-based configuration persistence
4. **Build Layer**: PyInstaller configuration for distribution

## Requirements

- Python 3.8+
- Windows 10/11 (for audio device support)
- Audio input device (microphone, line-in, etc.)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
