@echo off
chcp 65001 >nul
title SMMM Takip - Tum Degisiklikleri GitHub'a Push

echo.
echo  ==========================================================
echo   SMMM TAKIP - Tum Degisiklikleri Push Araci
echo  ==========================================================
echo.

set "ROOT=%~dp0.."
cd /d "%ROOT%"

where git >nul 2>&1
if errorlevel 1 (
    echo HATA: git bulunamadi. Lutfen Git kurun.
    pause
    exit /b 1
)

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"
if "%BRANCH%"=="" (
    echo HATA: Bu klasor bir git reposu degil.
    pause
    exit /b 1
)

echo Aktif branch: %BRANCH%
echo.

git status --short
echo.

git add -A
git diff --staged --quiet
if not errorlevel 1 (
    echo Commit edilecek degisiklik bulunamadi.
    pause
    exit /b 0
)

set "COMMIT_MSG="
set /p COMMIT_MSG=Commit mesaji (bos birakirsan varsayilan kullanilir): 
if "%COMMIT_MSG%"=="" set "COMMIT_MSG=chore: tum degisiklikleri guncelle"

echo.
echo Commit olusturuluyor...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo HATA: Commit basarisiz.
    pause
    exit /b 1
)

echo.
echo GitHub'a push ediliyor...
git push origin %BRANCH%
if errorlevel 1 (
    echo HATA: Push basarisiz.
    pause
    exit /b 1
)

echo.
echo BASARILI: Degisiklikler GitHub'a gonderildi.
pause
exit /b 0
