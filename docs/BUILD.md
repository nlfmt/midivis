# Building Audio Input Streamer

## Prerequisites

1. Python 3.8 or higher
2. All dependencies from requirements.txt
3. Convert `assets/icons/icon.svg` to `assets/icons/icon.ico` (64x64 pixels recommended)

## Converting SVG to ICO

You can use any of these methods to convert the provided `assets/icons/icon.svg` to `assets/icons/icon.ico`:

1. **Online converters**: 
   - https://convertio.co/svg-ico/
   - https://www.icoconverter.com/

2. **Inkscape** (free):
   - Open `assets/icons/icon.svg` in Inkscape
   - File → Export PNG Image (64x64 pixels)
   - Use online ICO converter on the PNG

3. **ImageMagick** (command line):
   ```bash
   magick assets/icons/icon.svg -resize 64x64 assets/icons/icon.ico
   ```

## Building the Executable

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Convert the icon** (if not done already):
   - Convert `assets/icons/icon.svg` to `assets/icons/icon.ico` and place it in the assets/icons folder

3. **Run the build script**:
   ```bash
   cd build
   build.bat
   ```

   Or manually:
   ```bash
   cd build
   pyinstaller AudioInputStreamer.spec
   ```

4. **Find your executable**:
   - The built executable will be in `build/dist/AudioInputStreamer.exe`

## Project Structure

```
sound_listener/
├── src/                          # Source code
│   ├── main.py                   # Main application entry point
│   ├── core/                     # Core functionality
│   └── ui/                       # User interface components
├── assets/                       # Static assets
│   └── icons/                    # Application icons
├── build/                        # Build configuration and scripts
├── docs/                         # Documentation
├── main.py                       # Root launcher script
└── requirements.txt              # Python dependencies
```

## Build Options

The PyInstaller spec file is configured for:
- **Single file executable** (everything bundled in one .exe)
- **No console window** (GUI only)
- **Icon included** (shows in taskbar and file explorer)
- **All dependencies bundled** (no need to install Python on target machine)

## Distribution

The resulting `AudioInputStreamer.exe` can be distributed as a standalone executable. Users don't need Python or any dependencies installed.

## Troubleshooting

- **Missing icon.ico**: Make sure to convert the SVG first and place it in `assets/icons/`
- **Build fails**: Check that all dependencies are installed correctly
- **Missing modules**: Add any missing imports to the `hiddenimports` list in the spec file
- **Import errors**: Ensure the relative import paths are correct in the source files
