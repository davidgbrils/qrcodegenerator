import qrcode
from PIL import Image, ImageTk
from PIL.Image import Resampling
import requests
from io import BytesIO
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import configparser
import telebot
import threading

class QRCodeGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator dengan Gambar di Tengah")
        self.root.geometry("400x550")
        self.root.resizable(False, False)
        self.qr_image = None
        self.qr_preview = None
        self.telegram_config_file = "telegram_config.ini"
        
        # Load or create telegram configuration
        self.telegram_token = ""
        self.telegram_chat_id = ""
        self.load_telegram_config()
        
        self.create_widgets()

    def create_widgets(self):
        # Input URL
        tk.Label(self.root, text="Masukkan URL tujuan QR Code:").pack(pady=5)
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.pack(pady=5)

        # Input Gambar
        tk.Label(self.root, text="Masukkan URL Gambar (misal: link GitHub raw):").pack(pady=5)
        self.img_entry = tk.Entry(self.root, width=50)
        self.img_entry.pack(pady=5)

        # Tombol Generate
        self.generate_btn = tk.Button(self.root, text="Buat QR Code", command=self.buat_qr, bg="green", fg="white")
        self.generate_btn.pack(pady=10)

        # Canvas untuk menampilkan hasil
        self.canvas_qr = tk.Canvas(self.root, width=250, height=250, bg='white')
        self.canvas_qr.pack(pady=10)

        # Tombol Simpan (ditampilkan setelah QR dibuat)
        self.save_btn = tk.Button(self.root, text="Simpan QR Code", bg="blue", fg="white")
        
        # Telegram settings button
        self.telegram_settings_btn = tk.Button(self.root, text="Pengaturan Telegram", command=self.open_telegram_settings)
        self.telegram_settings_btn.pack(pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Siap")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def generate_qr_code_with_image(self, url, image_url):
        try:
            self.status_var.set("Membuat QR Code...")
            self.root.update()
            
            # Buat QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Ambil gambar/logo dari URL
            response = requests.get(image_url)
            response.raise_for_status()
            logo = Image.open(BytesIO(response.content)).convert("RGBA")

            # Resize logo
            logo_size = int(qr_img.size[0] * 0.25)
            logo = logo.resize((logo_size, logo_size), Resampling.LANCZOS)

            # Tempel logo ke tengah QR code
            pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
            qr_img.paste(logo, pos, logo)
            
            self.status_var.set("QR Code berhasil dibuat")
            return qr_img

        except Exception as e:
            self.status_var.set("Error: " + str(e))
            messagebox.showerror("Error", f"Gagal membuat QR Code:\n{e}")
            return None

    def buat_qr(self):
        url = self.url_entry.get().strip()
        image_url = self.img_entry.get().strip()

        if not url or not image_url:
            messagebox.showwarning("Input Kosong", "Mohon masukkan URL dan URL Gambar!")
            return

        self.qr_image = self.generate_qr_code_with_image(url, image_url)

        if self.qr_image:
            # Tampilkan preview di canvas
            self.qr_preview = ImageTk.PhotoImage(self.qr_image.resize((250, 250)))
            self.canvas_qr.create_image(0, 0, anchor="nw", image=self.qr_preview)

            # Configure save button
            self.save_btn.config(command=self.save_and_send_qr)
            self.save_btn.pack(pady=5)

    def save_and_send_qr(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if filename:
            self.qr_image.save(filename)
            messagebox.showinfo("Berhasil", f"QR Code berhasil disimpan di:\n{filename}")
            
            # Send to Telegram if configured
            if self.telegram_token and self.telegram_chat_id:
                self.status_var.set("Mengirim ke Telegram...")
                self.root.update()
                threading.Thread(target=self.send_to_telegram, args=(filename,)).start()
            else:
                messagebox.showinfo("Info Telegram", "Pengaturan Telegram belum dikonfigurasi. Silakan atur di 'Pengaturan Telegram'")

    def send_to_telegram(self, file_path):
        try:
            bot = telebot.TeleBot(self.telegram_token)
            with open(file_path, 'rb') as photo:
                bot.send_photo(self.telegram_chat_id, photo, caption=f"QR Code: {self.url_entry.get()}")
            self.status_var.set("QR Code berhasil dikirim ke Telegram")
            messagebox.showinfo("Berhasil", "QR Code berhasil dikirim ke Telegram")
        except Exception as e:
            self.status_var.set("Gagal mengirim ke Telegram: " + str(e))
            messagebox.showerror("Error Telegram", f"Gagal mengirim ke Telegram:\n{e}")

    def load_telegram_config(self):
        config = configparser.ConfigParser()
        
        if os.path.exists(self.telegram_config_file):
            config.read(self.telegram_config_file)
            if 'Telegram' in config:
                self.telegram_token = config['Telegram'].get('token', '')
                self.telegram_chat_id = config['Telegram'].get('chat_id', '')

    def save_telegram_config(self):
        config = configparser.ConfigParser()
        config['Telegram'] = {
            'token': self.telegram_token,
            'chat_id': self.telegram_chat_id
        }
        
        with open(self.telegram_config_file, 'w') as f:
            config.write(f)

    def open_telegram_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Pengaturan Telegram")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)
        
        # Token field
        tk.Label(settings_window, text="Token Bot Telegram:").pack(pady=5)
        token_entry = tk.Entry(settings_window, width=50)
        token_entry.pack(pady=5)
        token_entry.insert(0, self.telegram_token)
        
        # Chat ID field
        tk.Label(settings_window, text="Chat ID Tujuan:").pack(pady=5)
        chat_id_entry = tk.Entry(settings_window, width=50)
        chat_id_entry.pack(pady=5)
        chat_id_entry.insert(0, self.telegram_chat_id)
        
        def save_settings():
            self.telegram_token = token_entry.get().strip()
            self.telegram_chat_id = chat_id_entry.get().strip()
            self.save_telegram_config()
            messagebox.showinfo("Berhasil", "Pengaturan Telegram berhasil disimpan")
            settings_window.destroy()
        
        save_button = tk.Button(settings_window, text="Simpan Pengaturan", command=save_settings, bg="blue", fg="white")
        save_button.pack(pady=10)
        
        # Panduan mendapatkan Token dan Chat ID
        help_button = tk.Button(
            settings_window, 
            text="Cara Mendapatkan Token & Chat ID", 
            command=lambda: messagebox.showinfo(
                "Panduan",
                "Untuk mendapatkan Token Bot:\n1. Chat dengan @BotFather di Telegram\n2. Buat bot baru dengan /newbot\n3. Salin token yang diberikan\n\nUntuk mendapatkan Chat ID:\n1. Chat dengan @userinfobot\n2. Salin ID yang diberikan"
            )
        )
        help_button.pack(pady=5)


if __name__ == "__main__":
    try:
        import telebot
    except ImportError:
        print("Menginstal pustaka yang diperlukan...")
        import subprocess
        subprocess.check_call(["pip", "install", "pyTelegramBotAPI"])
        import telebot
        
    root = tk.Tk()
    app = QRCodeGenerator(root)
    root.mainloop()