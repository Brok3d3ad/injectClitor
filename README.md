# MechsEarth Window Manager

A tool to manage window focus for MechsEarth application.

## Features

- Automatic window focus management
- Process detection and DLL injection
- User-friendly GUI interface
- Real-time process monitoring

## Files

- `gui.py` - The main GUI application
- `inject.c` - DLL source code for window management
- `injector.cpp` - DLL injection utility

## Building

### Prerequisites

- Python 3.x
- MinGW-w64 (for C/C++ compilation)
- PyInstaller

### Compilation Steps

1. Compile the DLL:
```bash
gcc -shared -o final/active_window.dll inject.c -luser32
```

2. Compile the injector:
```bash
g++ injector.cpp -o final/injector.exe -O2 -static -s -DNDEBUG -luser32
```

3. Build the GUI:
```bash
cd final
pyinstaller --noconsole --icon=logo.ico --add-data "logo.png;." --add-data "logo.ico;." --add-data "active_window.dll;." --add-data "injector.exe;." gui.py
```

## Usage

1. Run the compiled executable from the `dist` folder
2. Click "Refresh PIDs" to find running MechsEarth processes
3. Click "Inject All" to apply window management

## Notes

- Requires administrative privileges for DLL injection
- All files must be kept in the same directory as the executable
- The application will automatically manage window focus after injection 