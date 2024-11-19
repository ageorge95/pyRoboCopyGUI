call activate.bat
python -m pip install --upgrade pyinstaller
rem pyinstaller --windowed --icon=icon.ico main.py
pyinstaller main.spec
pause