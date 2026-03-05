@echo off
echo ======================================
echo   QR Code Generator - Build EXE
echo ======================================
echo.

echo [1/2] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [2/2] Building EXE with PyInstaller...
pyinstaller generate_qr_code_tele.spec --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ======================================
echo   Build BERHASIL!
echo   File EXE ada di: dist\QRCodeGenerator.exe
echo ======================================
pause
