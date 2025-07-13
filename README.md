Use `pyinstaller` in the **root directory of this repository** to compile the Python source code into an executable:
```bash
pyinstaller Booker.spec
```
The `--icon=assets/Booker.ico` option only works on Windows. Convert the icon to a `.icns` file for macOS or use a different method for Linux.