# Publish QR Code Generator

## File yang dibagikan ke pengguna

Bagikan file ini:

```text
dist\QRCodeGeneratorSetup.exe
```

Pengguna cukup double-click file setup tersebut. Aplikasi akan dipasang ke:

```text
%LocalAppData%\Programs\QRCodeGenerator
```

Installer juga membuat shortcut di Desktop dan Start Menu. Aplikasi bisa dihapus dari Windows Settings > Apps, atau dengan menjalankan:

```text
%LocalAppData%\Programs\QRCodeGenerator\uninstall.ps1
```

## Build dari source

1. Build EXE aplikasi:

```bat
build.bat
```

2. Build installer setup:

```bat
build_setup.bat
```

Hasil akhirnya ada di:

```text
dist\QRCodeGeneratorSetup.exe
```

## Catatan

Installer ini memakai compiler C# bawaan Windows, jadi tidak perlu install Inno Setup atau NSIS.
