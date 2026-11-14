@echo off
rem Yerel sunucu: tarayici dosyalari fetch ile okuyabilsin diye (internet gerekmez).
cd /d "%~dp0"
start "" http://localhost:8765/index.html
python -m http.server 8765
