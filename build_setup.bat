@echo off
echo ======================================
echo   QR Code Generator - Build Setup
echo ======================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_setup.ps1"
if errorlevel 1 (
    echo.
    echo ERROR: Gagal membuat setup installer.
    pause
    exit /b 1
)

echo.
echo ======================================
echo   Setup BERHASIL!
echo   File setup ada di: dist\QRCodeGeneratorSetup.exe
echo ======================================
pause
