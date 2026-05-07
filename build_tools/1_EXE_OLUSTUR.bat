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
set "BUILD_PYTHON=%~dp0.venv\Scripts\python.exe"

set "INNO_COMPILER=C:\Users\selim\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

cd /d "%ROOT%"
for /f "tokens=*" %%i in ('%PYTHON% -c "from version import APP_VERSION; print(APP_VERSION)"') do set APP_VERSION=%%i
if "%APP_VERSION%"=="" set APP_VERSION=1.0.0
echo Sürüm: %APP_VERSION%

cd /d "%ROOT%"

:: ── ADIM 1: İkonu yenile ──
echo [1/5] İkon oluşturuluyor...
"%PYTHON%" build_tools\create_icon.py
if errorlevel 1 (
    echo HATA: İkon oluşturulamadı!
    goto :hata
)
echo       ✓ İkon hazır
echo.

:: ── ADIM 2: Build .venv bağımlılıklarını güncelle ──
echo [2/5] Build ortamı bağımlılıkları yükleniyor...
if not exist "%BUILD_PYTHON%" (
    echo UYARI: build_tools\.venv bulunamadi, yeniden olusturuluyor...
    "%PYTHON%" -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo HATA: build_tools\.venv olusturulamadi!
        goto :hata
    )
)

"%BUILD_PYTHON%" -m ensurepip --upgrade
if errorlevel 1 (
    echo UYARI: ensurepip adimi basarisiz oldu, pip kontrolu yapiliyor...
)

"%BUILD_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo UYARI: pip bulunamadi, build ortamı sifirdan olusturuluyor...
    if exist "%~dp0.venv" rmdir /s /q "%~dp0.venv"
    "%PYTHON%" -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo HATA: build_tools\.venv yeniden olusturulamadi!
        goto :hata
    )
    "%BUILD_PYTHON%" -m ensurepip --upgrade
)

"%BUILD_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo HATA: pip guncellenemedi!
    goto :hata
)

"%BUILD_PYTHON%" -m pip install -r "%ROOT%\requirements.txt"
if errorlevel 1 (
    echo HATA: Build bagimliliklari yuklenemedi!
    goto :hata
)

if not exist "%PYINSTALLER%" (
    echo UYARI: PyInstaller build ortamında yok, yukleniyor...
    "%BUILD_PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo HATA: PyInstaller yuklenemedi!
        goto :hata
    )
)

echo       ✓ Build bağımlılıkları hazır
echo.

:: ── ADIM 3: PyInstaller ile exe paketi oluştur ──
echo [3/5] PyInstaller ile uygulama paketleniyor...
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

:: ── ADIM 4: Inno Setup ile kurulum EXE oluştur ──
echo [4/5] Kurulum dosyası oluşturuluyor (Inno Setup)...

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

:: ── ADIM 5: Sonuç ──
echo [5/5] Tamamlandı!
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
