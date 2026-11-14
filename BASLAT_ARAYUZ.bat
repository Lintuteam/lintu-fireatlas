@echo off
title NASA MODIS-VIIRS Turkiye Yangin Aktivite Takvimi v2
cd /d "%~dp0arayuz"
echo Yerel web sunucusu baslatiliyor: http://localhost:8765
echo Kapatmak icin bu pencereyi kapatin veya Ctrl+C basin.
start "" "http://localhost:8765"
python -m http.server 8765
pause
