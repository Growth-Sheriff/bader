@echo off
REM BADER Derneği - Kurulum Script'i (Windows)

echo ================================================
echo BADER Dernegi Kurulum Baslatiliyor...
echo ================================================
echo.

REM Python kontrolü
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python bulunamadi! Lutfen Python 3.8 veya uzeri kurun.
    pause
    exit /b 1
)

echo [+] Python bulundu
echo.

REM pip kontrolü
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip bulunamadi! Lutfen pip kurun.
    pause
    exit /b 1
)

echo [+] pip bulundu
echo.

REM Sanal ortam oluştur
set /p create_venv="Sanal ortam (virtual environment) olusturulsun mu? (e/h): "

if /i "%create_venv%"=="e" (
    echo [*] Sanal ortam olusturuluyor...
    python -m venv venv
    
    call venv\Scripts\activate.bat
    echo [+] Sanal ortam aktiflestirildi
    echo.
)

echo [*] Gerekli kutuphaneler yukleniyor...
echo.

REM Bağımlılıkları yükle
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo [+] Kurulum basariyla tamamlandi!
    echo ================================================
    echo.
    echo Programi baslatmak icin:
    
    if /i "%create_venv%"=="e" (
        echo   venv\Scripts\activate.bat  REM (Sanal ortami aktifleştir)
    )
    
    echo   python main.py
    echo.
) else (
    echo.
    echo [X] Kurulum sirasinda hata olustu!
    echo Lutfen hata mesajlarini kontrol edin.
    pause
    exit /b 1
)

pause


