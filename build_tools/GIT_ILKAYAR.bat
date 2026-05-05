@echo off
chcp 65001 >nul
title SMMM Takip — GitHub İlk Kurulum

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║       SMMM TAKİP — GitHub İlk Kurulum                  ║
echo  ║  Bu scripti SADECE BİR KEZ çalıştırın.                 ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "ROOT=%~dp0.."
set "PYTHON=C:\Users\selim\.local\bin\python3.14.exe"
cd /d "%ROOT%"

:: ── GitHub CLI kontrolü ──
where gh >nul 2>&1
if errorlevel 1 (
    echo  ╔══════════════════════════════════════════════════════════╗
    echo  ║  GitHub CLI bulunamadı. Kuruluyor...                    ║
    echo  ╚══════════════════════════════════════════════════════════╝
    winget install --id GitHub.cli -e --silent
    if errorlevel 1 (
        echo  HATA: Otomatik kurulum başarısız.
        echo  Elle kurun: https://cli.github.com
        pause
        exit /b 1
    )
    echo  ✓ GitHub CLI kuruldu. Terminal yeniden başlatılabilir.
)

:: ── Git kontrolü ──
where git >nul 2>&1
if errorlevel 1 (
    echo  Git bulunamadı. Kuruluyor...
    winget install --id Git.Git -e --silent
    echo  Git kuruldu. Lütfen bu scripti yeniden çalıştırın.
    pause
    exit /b 1
)

echo  Adım 1/5: GitHub'a giriş yapılıyor...
echo  (Tarayıcı açılacak — GitHub hesabınızla giriş yapın)
echo.
gh auth login --web --git-protocol https
if errorlevel 1 (
    echo  HATA: GitHub girişi başarısız!
    goto :hata
)
echo.

echo  Adım 2/5: GitHub repo bilgilerini girin
echo  ─────────────────────────────────────────
echo.
set /p GH_USER=GitHub kullanıcı adınız (örnek: selimcan): 
set /p GH_REPO=Repo adı (örnek: smmm-takip): 
echo.

if "%GH_USER%"=="" goto :eksik_bilgi
if "%GH_REPO%"=="" goto :eksik_bilgi

:: ── version.py'yi güncelle ──
echo  Adım 3/5: version.py güncelleniyor...
powershell -NoProfile -Command ^
    "(Get-Content '%ROOT%\version.py' -Encoding UTF8) -replace 'GITHUB_KULLANICISI/smmm-takip', '%GH_USER%/%GH_REPO%' | Set-Content '%ROOT%\version.py' -Encoding UTF8"
if errorlevel 1 (
    echo  HATA: version.py güncellenemedi!
    goto :hata
)
echo  ✓ GITHUB_REPO = %GH_USER%/%GH_REPO% olarak ayarlandı

:: ── licenses.json'ı kendi admin kullanıcın için güncelle ──
echo.
set /p ADMIN_USER=Yönetici kullanıcı adı (kendi kullanıcı adınız, örnek: admin): 
if not "%ADMIN_USER%"=="" (
    powershell -NoProfile -Command ^
        "(Get-Content '%ROOT%\licenses.json' -Encoding UTF8) -replace '\"admin\"', '\"%ADMIN_USER%\"' | Set-Content '%ROOT%\licenses.json' -Encoding UTF8"
    echo  ✓ Yönetici kullanıcı adı '%ADMIN_USER%' olarak ayarlandı
)
echo.

:: ── Git repo başlat ──
echo  Adım 4/5: Git repo başlatılıyor...
if exist "%ROOT%\.git" (
    echo  ✓ Git repo zaten mevcut, geçiliyor...
) else (
    git init
    echo  ✓ Git repo oluşturuldu
)

git add .
git commit -m "ilk sürüm: SMMM Takip v1.0.0"
echo  ✓ Commit oluşturuldu
echo.

:: ── GitHub'da repo oluştur ve push et ──
echo  Adım 5/5: GitHub'da repo oluşturuluyor ve yükleniyor...
echo  (Repo görünürlüğü: public — lisans dosyasına tüm istemciler erişebilir)
echo.

gh repo create %GH_USER%/%GH_REPO% --public --source=. --remote=origin --push
if errorlevel 1 (
    echo.
    echo  Repo zaten varsa mevcut remote'a push deneyin:
    git remote add origin https://github.com/%GH_USER%/%GH_REPO%.git 2>nul
    git branch -M master
    git push -u origin master
    if errorlevel 1 goto :hata
)

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✅  Tamamlandı!                                         ║
echo  ║                                                          ║
echo  ║  GitHub repo : https://github.com/%GH_USER%/%GH_REPO%
echo  ║                                                          ║
echo  ║  Sonraki adımlar:                                        ║
echo  ║  1) BUILD_KURULUM.bat ile yeni EXE oluşturun            ║
echo  ║  2) Yeni kullanıcı eklemek için licenses.json           ║
echo  ║     dosyasını GitHub'da düzenleyin                      ║
echo  ║  3) RELEASE_GITHUB.bat ile yeni sürüm yayınlayın       ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: Repo sayfasını tarayıcıda aç
gh repo view --web 2>nul

pause
exit /b 0

:eksik_bilgi
echo  HATA: Kullanıcı adı ve repo adı boş bırakılamaz!
goto :hata

:hata
echo.
echo  İşlem başarısız. Yukarıdaki hataları inceleyin.
pause
exit /b 1
