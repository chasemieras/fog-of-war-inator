# The Fog-Of-War-Inator

A simple app for TTRPGs that allows a DM to hide their battle maps using fog of war mechanics.

*Note:* This tool was written with the help of Generative AI. The basic layouts of this application were created by myself, but the drawing was made with Gen AI.

## Features

- **Dual View System**: Separate DM and Player windows
- **Interactive Fog Revealing**: Click and drag to reveal map areas
- **Auto-Save/Load**: Automatic fog state management
- **Fullscreen Support**: F11 to toggle fullscreen on both windows
- **Undo/Redo**: Ctrl+Z/Ctrl+Y to undo/redo fog changes
- **Adjustable Reveal Size**: Configurable brush size for revealing fog
- **Keyboard Shortcuts**: Full keyboard control for efficient gameplay

## Controls

### DM Window

- **Left Click/Drag**: Reveal fog areas
- **Ctrl + S**: Manual save fog state
- **Ctrl + Z**: Undo last action
- **Ctrl + Y**: Redo last undone action
- **F11**: Toggle fullscreen
- **Esc**: Exit fullscreen
- **F1**: Show help (if working, otherwise try F2 or Ctrl+H)

### Control Panel

- **Load Map Image**: Import your battle map
- **Save/Load Fog State**: Manual fog state management
- **Reveal Size Slider**: Adjust the size of revealed areas
- **Reset/Clear Fog**: Reset to full fog or clear all fog

## Tech Stack

Written in Python with:

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [pillow](https://python-pillow.org/) - Image processing
- [numpy](https://numpy.org/) - Array operations
- [opencv-python](https://opencv.org/) - Computer vision and image manipulation
- [tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework (built-in)

## Getting Started

1. Clone or download the repository
2. Open the code in VS Code or your preferred editor
3. Open the terminal and enter the following commands:

   ```bash
   python3 -m venv fowi
   source fowi/bin/activate
   pip3 install customtkinter pillow numpy opencv-python
   ```

4. Run the application:

   ```bash
   python3 app.py
   ```

## Building the App

To create a standalone executable:

1. Ensure you are in the venv for fowi:

   ```bash
   source fowi/bin/activate 
   ```

2. Install pyinstaller in the venv:

   ```bash
   pip install pyinstaller
   ```

3. Build the executable:

   ```bash
   pyinstaller --noconfirm --onefile --windowed app.py
   ```

The executable will be created in the `dist/` folder.

## File Structure

The app automatically creates a `fog/` directory next to your map images to store fog states:

``` File
your_maps/
├── dungeon_map.png
├── forest_encounter.jpg
└── fog/
    ├── dungeon_map.fog
    └── forest_encounter.fog
```

## Usage Tips

1. **Load your map image first** through the control panel
2. **Open both DM and Player windows** - position them on separate monitors if available
3. **Use fullscreen mode** (F11) for immersive gameplay
4. **Fog states auto-save** when you close windows
5. **Use Ctrl+S** to manually save at any time
6. **Experiment with reveal sizes** to find what works best for your maps
