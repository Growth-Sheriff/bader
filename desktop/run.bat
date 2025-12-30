@echo off
REM BADER Derneği - Çalıştırma Script'i (Windows)

REM Sanal ortam varsa aktifleştir
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Programı çalıştır
python main.py

pause


