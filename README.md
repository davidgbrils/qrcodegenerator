# QR Code Generator

Aplikasi desktop Windows untuk membuat QR Code dari URL, dengan pilihan menambahkan logo di tengah QR Code, mengganti warna, menyimpan hasil sebagai gambar, dan mengirim hasil ke Telegram jika bot sudah dikonfigurasi.

## Download dan Install

Gunakan file installer berikut:

```text
dist\QRCodeGeneratorSetup.exe
```

Cara install:

1. Double-click `QRCodeGeneratorSetup.exe`.
2. Tunggu sampai proses install selesai.
3. Buka aplikasi dari shortcut Desktop atau Start Menu.

Aplikasi akan terpasang di:

```text
%LocalAppData%\Programs\QRCodeGenerator
```

## Cara Menggunakan

1. Buka aplikasi **QR Code Generator**.
2. Masukkan URL tujuan QR Code, misalnya `https://example.com`.
3. Pilih logo jika diperlukan:
   - Masukkan URL gambar, atau
   - Klik **Pilih File Lokal** untuk memilih gambar dari komputer.
4. Pilih warna foreground/background QR Code jika ingin diganti.
5. Klik **Buat QR Code**.
6. Klik **Simpan** untuk menyimpan hasil QR Code sebagai PNG/JPG.

## Fitur Telegram

Fitur Telegram bersifat opsional.

Untuk mengaktifkan:

1. Klik tombol **Telegram** di aplikasi.
2. Masukkan **Token Bot Telegram**.
3. Masukkan **Chat ID Tujuan**.
4. Simpan pengaturan.

Setelah itu, ketika QR Code disimpan, aplikasi dapat mengirim gambar QR Code ke Telegram.

## Build dari Source

Install dependency:

```bat
pip install -r requirements.txt
```

Build EXE:

```bat
build.bat
```

Build installer:

```bat
build_setup.bat
```

Hasil build:

```text
dist\QRCodeGenerator.exe
dist\QRCodeGeneratorSetup.exe
```

## Catatan Keamanan

Jangan commit token Telegram pribadi ke GitHub. File `telegram_config.ini` di repository cukup dibiarkan kosong, lalu pengguna mengisi token dari menu Telegram di aplikasi.
