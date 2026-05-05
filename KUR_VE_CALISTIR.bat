@echo off
chcp 65001 > nul
title SMMM Takip - Kurulum ve Başlatma

echo ============================================
echo   SMMM Takip Sistemi - İlk Kurulum
echo ============================================
echo.

:: Python kontrolü
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] Python bulunamadi!
    echo.
    echo Lutfen once Python kurun:
    echo   https://www.python.org/downloads/
    echo   (Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin)
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python bulundu:
python --version
echo.

:: PyQt5 kurulumu
echo PyQt5 kuruluyor...
python -m pip install PyQt5 -q
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] PyQt5 kurulamadi. Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)
echo [OK] PyQt5 kuruldu.
echo.

echo Uygulama baslatiliyor...
python main.py
pause
