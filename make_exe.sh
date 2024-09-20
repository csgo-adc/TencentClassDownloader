rm -rf build main.exe main.spec

pyinstaller -F main.py

mv dist/main.exe .

rm -rf build dist __pycache__ main.spec