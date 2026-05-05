@echo off
chcp 65001 >nul
title SMMM Takip — GitHub'a Yeni Sürüm Yayınla

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║       SMMM TAKİP — GitHub Release Oluşturucu           ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "ROOT=%~dp0.."
set "PYTHON=C:\Users\selim\.local\bin\python3.14.exe"
cd /d "%ROOT%"

:: ── Gereksinim: GitHub CLI (gh) kurulu mu? ──
where gh >nul 2>&1
if errorlevel 1 (
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║  HATA: GitHub CLI (gh) bulunamadı!                      ║
    echo  ║                                                          ║
    echo  ║  Kurulum için:                                           ║
    echo  ║    winget install --id GitHub.cli                       ║
    echo  ║  veya: https://cli.github.com                           ║
    echo  ║                                                          ║
    echo  ║  Kurulunca tekrar çalıştırın.                           ║
    echo  ╚══════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

:: ── Sürümü version.py'den oku ──
for /f "tokens=*" %%i in ('%PYTHON% -c "from version import APP_VERSION; print(APP_VERSION)"') do set APP_VERSION=%%i
if "%APP_VERSION%"=="" (
    echo HATA: Sürüm okunamadı!
    pause
    exit /b 1
)

:: ── GitHub repo bilgisini version.py'den oku ──
for /f "tokens=*" %%i in ('%PYTHON% -c "from version import GITHUB_REPO; print(GITHUB_REPO)"') do set GITHUB_REPO=%%i
if "%GITHUB_REPO%"=="GITHUB_KULLANICISI/smmm-takip" (
    echo.
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║  HATA: version.py dosyasında GITHUB_REPO ayarlanmamış!  ║
    echo  ║                                                          ║
    echo  ║  version.py içindeki GITHUB_REPO satırını               ║
    echo  ║  kendi GitHub repo adresinizle değiştirin.              ║
    echo  ║  Örnek: "selimcan/smmm-takip"                           ║
    echo  ╚══════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

echo  Sürüm    : v%APP_VERSION%
echo  GitHub   : %GITHUB_REPO%
echo.

:: ── Kullanıcı onayı ──
set /p ONAY=  Bu sürümü GitHub'a yayınlamak istiyor musunuz? (E/H): 
if /i not "%ONAY%"=="E" (
    echo İptal edildi.
    pause
    exit /b 0
)

echo.

:: ── ADIM 1: Mevcut kurulum EXE'yi bul ──
echo [1/5] Kurulum dosyası aranıyor...
set "INSTALLER=%ROOT%\installer_output\SMMTakip_Kurulum_v%APP_VERSION%.exe"
if not exist "%INSTALLER%" (
    echo  Kurulum EXE bulunamadı: %INSTALLER%
    echo  Önce BUILD_KURULUM.bat çalıştırın.
    echo.
    set /p BUILD_ONAY=  Şimdi build yapılsın mı? (E/H): 
    if /i "%BUILD_ONAY%"=="E" (
        call "%ROOT%\build_tools\1_EXE_OLUSTUR.bat"
        if errorlevel 1 goto :hata
    ) else (
        goto :hata
    )
)
if not exist "%INSTALLER%" (
    echo HATA: Kurulum dosyası hâlâ bulunamadı!
    goto :hata
)
echo       ✓ Kurulum dosyası hazır
echo.

:: ── ADIM 2: git ile değişiklikleri commit et ──
echo [2/5] Git commit kontrol ediliyor...
git status --short >nul 2>&1
if errorlevel 1 (
    echo  UYARI: Git repo bulunamadı. Devam ediliyor...
    goto :tag_olustur
)

git add -A
git diff --staged --quiet
if not errorlevel 1 (
    echo       ✓ Commit edilecek değişiklik yok
    goto :tag_olustur
)

git commit -m "chore: release v%APP_VERSION%"
if errorlevel 1 (
    echo HATA: git commit başarısız!
    goto :hata
)
echo       ✓ Commit oluşturuldu

git push
if errorlevel 1 (
    echo UYARI: git push başarısız. Devam ediliyor...
)
echo.

:tag_olustur
:: ── ADIM 3: Git tag oluştur ──
echo [3/5] Git tag oluşturuluyor...
git tag -a "v%APP_VERSION%" -m "Release v%APP_VERSION%" 2>nul
if errorlevel 1 (
    echo  UYARI: Tag zaten mevcut olabilir. Devam ediliyor...
) else (
    echo       ✓ Tag v%APP_VERSION% oluşturuldu
)

git push origin "v%APP_VERSION%" 2>nul
echo.

:: ── ADIM 4: GitHub Release oluştur ve EXE yükle ──
echo [4/5] GitHub Release oluşturuluyor ve dosya yükleniyor...
echo       (Bu adım biraz sürebilir, internet hızına bağlı...)
echo.

gh release create "v%APP_VERSION%" ^
    "%INSTALLER%" ^
    --repo "%GITHUB_REPO%" ^
    --title "SMMM Takip v%APP_VERSION%" ^
    --generate-notes

if errorlevel 1 (
    echo.
    echo HATA: GitHub Release oluşturulamadı!
    echo.
    echo Olası nedenler:
    echo  - gh auth login yapılmamış (komut: gh auth login)
    echo  - Tag zaten release'e bağlı (önceki release'i silin)
    echo  - İnternet bağlantısı yok
    goto :hata
)
echo.
echo       ✓ GitHub Release yayınlandı!
echo.

:: ── ADIM 5: Tamamlandı ──
echo [5/5] Tamamlandı!
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✅  v%APP_VERSION% başarıyla GitHub'a yayınlandı!
echo  ║                                                          ║
echo  ║  Kullanıcılar uygulamayı açtıklarında otomatik          ║
echo  ║  güncelleme bildirimi alacaklar.                        ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: Tarayıcıda release sayfasını aç
gh release view "v%APP_VERSION%" --web --repo "%GITHUB_REPO%" 2>nul

pause
exit /b 0

:hata
echo.
echo  Bir hata oluştu. Yukarıdaki mesajları inceleyin.
pause
exit /b 1
