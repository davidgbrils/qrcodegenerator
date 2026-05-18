# QR Code Generator

Aplikasi desktop Windows untuk membuat QR Code dari URL. Aplikasi mendukung sampai 3 link sekaligus, nama file custom untuk tiap QR Code, logo di tengah QR Code, pilihan warna, export ZIP, dan pengiriman ZIP ke Telegram jika bot sudah dikonfigurasi.

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
2. Masukkan 1 sampai 3 URL tujuan QR Code, misalnya `https://example.com`.
3. Isi **Nama file** untuk setiap QR Code. Nama ini akan dipakai sebagai nama file PNG di dalam ZIP.
4. Pilih logo jika diperlukan:
   - Masukkan URL gambar, atau
   - Klik **Pilih File Lokal** untuk memilih gambar dari komputer.
5. Pilih warna foreground/background QR Code jika ingin diganti.
6. Klik **Buat QR Code**.
7. Klik **Export ZIP** untuk menyimpan semua QR Code yang dibuat ke dalam satu file ZIP.

Contoh isi ZIP:

```text
promo_instagram.png
form_pendaftaran.png
website_utama.png
```

## Fitur Telegram

Fitur Telegram bersifat opsional.

Untuk mengaktifkan:

1. Klik tombol **Telegram** di aplikasi.
2. Masukkan **Token Bot Telegram**.
3. Masukkan **Chat ID Tujuan**.
4. Simpan pengaturan.

Setelah itu, ketika ZIP diexport, aplikasi dapat mengirim file ZIP QR Code ke Telegram.

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
