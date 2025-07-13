Use `pyinstaller` in the **root directory of this repository** to compile the Python source code into an executable:
```bash
pyinstaller Booker.spec
```
The option for icons in `Booker.spec` is set to `icon=['assets\\Booker.ico']`, which only works on Windows.