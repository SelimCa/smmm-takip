@echo off
chcp 65001 >nul
title SMMM Takip — Kurulum Dosyası Oluşturucu

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║         SMMM TAKİP — EXE KURULUM OLUŞTURUCU         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: Kök dizin (bu bat dosyasının bir üst klasörü)
set "ROOT=%~dp0.."
set "PYTHON=C:\Users\selim\.local\bin\python3.14.exe"
set "PYINSTALLER=%~dp0.venv\Scripts\pyinstaller.exe"

set "INNO_COMPILER=C:\Users\selim\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

cd /d "%ROOT%"
for /f "tokens=*" %%i in ('%PYTHON% -c "from version import APP_VERSION; print(APP_VERSION)"') do set APP_VERSION=%%i
if "%APP_VERSION%"=="" set APP_VERSION=1.0.0
echo Sürüm: %APP_VERSION%

cd /d "%ROOT%"

:: ── ADIM 1: İkonu yenile ──
echo [1/4] İkon oluşturuluyor...
"%PYTHON%" build_tools\create_icon.py
if errorlevel 1 (
    echo HATA: İkon oluşturulamadı!
    goto :hata
)
echo       ✓ İkon hazır
echo.

:: ── ADIM 2: PyInstaller ile exe paketi oluştur ──
echo [2/4] PyInstaller ile uygulama paketleniyor...
echo       (Bu adım birkaç dakika sürebilir...)
echo.

:: Önceki dist ve build temizle
if exist "dist\SMMM_Takip" rmdir /s /q "dist\SMMM_Takip"
if exist "build\SMMM_Takip" rmdir /s /q "build\SMMM_Takip"

"%PYINSTALLER%" --noconfirm ^
    --distpath "%ROOT%\dist" ^
    --workpath "%ROOT%\build" ^
    --log-level WARN ^
    "%ROOT%\build_tools\smmm_takip.spec"

if errorlevel 1 (
    echo.
    echo HATA: PyInstaller başarısız!
    goto :hata
)

:: data klasörünü dist'e ekleme — boş olarak oluştur (kullanıcı verisi OLMADAN)
if not exist "dist\SMMM_Takip\data" mkdir "dist\SMMM_Takip\data"
:: .gitkeep ekle ki klasör kurulumda oluşsun
echo. > "dist\SMMM_Takip\data\.gitkeep"

echo       ✓ Paketleme tamamlandı
echo.

:: ── ADIM 3: Inno Setup ile kurulum EXE oluştur ──
echo [3/4] Kurulum dosyası oluşturuluyor (Inno Setup)...

:: Çıktı klasörü
if not exist "%ROOT%\installer_output" mkdir "%ROOT%\installer_output"

if not exist "%INNO_COMPILER%" (
    echo.
    echo  ╔══════════════════════════════════════════════════════╗
    echo  ║  UYARI: Inno Setup 6 bulunamadı!                    ║
    echo  ║  Lütfen şu adresten indirip kurun:                  ║
    echo  ║  https://jrsoftware.org/isdl.php                    ║
    echo  ║                                                      ║
    echo  ║  Kurduktan sonra bu dosyayı tekrar çalıştırın.      ║
    echo  ╚══════════════════════════════════════════════════════╝
    echo.
    echo  PyInstaller çıktısı hazır: dist\SMMM_Takip\
    echo  Inno Setup kurulunca kurulum EXE'si de oluşturulacak.
    pause
    exit /b 0
)

"%INNO_COMPILER%" /DMyAppVersion=%APP_VERSION% "%ROOT%\build_tools\setup_script.iss"

if errorlevel 1 (
    echo HATA: Inno Setup başarısız!
    goto :hata
)

echo       ✓ Kurulum EXE hazır
echo.

:: ── ADIM 4: Sonuç ──
echo [4/4] Tamamlandı!
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  ✅  Kurulum dosyası oluşturuldu!                    ║
echo  ║                                                      ║
echo  ║  Konum: installer_output\                            ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

explorer "%ROOT%\installer_output"
pause
exit /b 0

:hata
echo.
echo  Oluşan hata yukarıda gösterilmektedir.
pause
exit /b 1
