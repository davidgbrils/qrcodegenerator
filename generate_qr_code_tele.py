import qrcode
from PIL import Image, ImageTk, ImageDraw
from PIL.Image import Resampling
import requests
from io import BytesIO
import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
import os
import sys
import configparser
import telebot
import threading

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.tooltip import ToolTip
    HAS_TTKBOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    HAS_TTKBOOTSTRAP = False


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


class QRCodeGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator")
        self.root.geometry("820x620")
        self.root.minsize(820, 620)
        self.qr_image = None
        self.qr_preview = None
        self.telegram_config_file = self._get_config_path("telegram_config.ini")
        self.history_file = self._get_config_path("url_history.txt")

        # QR Colors
        self.fg_color = "#000000"
        self.bg_color = "#FFFFFF"

        # Image source
        self.local_image_path = None

        # Load or create telegram configuration
        self.telegram_token = ""
        self.telegram_chat_id = ""
        self.load_telegram_config()

        # URL history
        self.url_history = self.load_url_history()

        self.create_widgets()

    def _get_config_path(self, filename):
        """Get config file path that works both in dev and exe mode."""
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), filename)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    # ─── URL History ───────────────────────────────────────────────
    def load_url_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()][-10:]
        return []

    def save_url_history(self, url):
        if url and url not in self.url_history:
            self.url_history.append(url)
            self.url_history = self.url_history[-10:]
            with open(self.history_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.url_history))

    # ─── Widgets ───────────────────────────────────────────────────
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # ── Left Panel ──
        left_panel = ttk.Labelframe(main_frame, text="  ⚙ Pengaturan QR Code  ", padding=15)
        left_panel.pack(side=LEFT, fill=BOTH, expand=False, padx=(0, 10))

        # URL Input
        ttk.Label(left_panel, text="URL Tujuan QR Code:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        self.url_entry = ttk.Entry(left_panel, width=38, font=("Segoe UI", 10))
        self.url_entry.pack(fill=X, pady=(0, 5))
        self.url_entry.insert(0, "https://")

        # History Combobox
        if self.url_history:
            ttk.Label(left_panel, text="Riwayat URL:", font=("Segoe UI", 9)).pack(anchor=W, pady=(0, 2))
            self.history_combo = ttk.Combobox(left_panel, values=self.url_history, width=36, font=("Segoe UI", 9), state="readonly")
            self.history_combo.pack(fill=X, pady=(0, 8))
            self.history_combo.bind("<<ComboboxSelected>>", self._on_history_select)

        # ── Separator ──
        ttk.Separator(left_panel, orient=HORIZONTAL).pack(fill=X, pady=8)

        # Image Source Section
        ttk.Label(left_panel, text="Logo di Tengah QR:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))

        # Image URL
        ttk.Label(left_panel, text="URL Gambar:", font=("Segoe UI", 9)).pack(anchor=W, pady=(0, 2))
        self.img_entry = ttk.Entry(left_panel, width=38, font=("Segoe UI", 10))
        self.img_entry.pack(fill=X, pady=(0, 5))

        # OR label
        ttk.Label(left_panel, text="─── atau ───", font=("Segoe UI", 9), foreground="gray").pack(pady=4)

        # Local file picker
        self.local_file_label = ttk.Label(left_panel, text="Belum ada file dipilih", font=("Segoe UI", 8), foreground="gray", wraplength=280)
        browse_frame = ttk.Frame(left_panel)
        browse_frame.pack(fill=X, pady=(0, 3))

        if HAS_TTKBOOTSTRAP:
            browse_btn = ttk.Button(browse_frame, text="📁 Pilih File Lokal", command=self.pick_local_image, bootstyle="outline")
            clear_btn = ttk.Button(browse_frame, text="✕", command=self.clear_local_image, bootstyle="outline-danger", width=3)
        else:
            browse_btn = ttk.Button(browse_frame, text="📁 Pilih File Lokal", command=self.pick_local_image)
            clear_btn = ttk.Button(browse_frame, text="✕", command=self.clear_local_image, width=3)

        browse_btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 4))
        clear_btn.pack(side=RIGHT)

        self.local_file_label.pack(anchor=W, pady=(0, 5))

        # ── Separator ──
        ttk.Separator(left_panel, orient=HORIZONTAL).pack(fill=X, pady=8)

        # Color options
        ttk.Label(left_panel, text="Warna QR Code:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))

        color_frame = ttk.Frame(left_panel)
        color_frame.pack(fill=X, pady=(0, 8))

        # Foreground color
        fg_frame = ttk.Frame(color_frame)
        fg_frame.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        ttk.Label(fg_frame, text="Foreground:", font=("Segoe UI", 9)).pack(anchor=W)
        self.fg_canvas = tk.Canvas(fg_frame, width=60, height=26, bg=self.fg_color, cursor="hand2",
                                    bd=1, relief="solid", highlightthickness=0)
        self.fg_canvas.pack(anchor=W, pady=2)
        self.fg_canvas.bind("<Button-1>", lambda e: self.pick_color("fg"))

        # Background color
        bg_frame = ttk.Frame(color_frame)
        bg_frame.pack(side=LEFT, expand=True, fill=X)
        ttk.Label(bg_frame, text="Background:", font=("Segoe UI", 9)).pack(anchor=W)
        self.bg_canvas = tk.Canvas(bg_frame, width=60, height=26, bg=self.bg_color, cursor="hand2",
                                    bd=1, relief="solid", highlightthickness=0)
        self.bg_canvas.pack(anchor=W, pady=2)
        self.bg_canvas.bind("<Button-1>", lambda e: self.pick_color("bg"))

        # ── Separator ──
        ttk.Separator(left_panel, orient=HORIZONTAL).pack(fill=X, pady=8)

        # Generate Button
        if HAS_TTKBOOTSTRAP:
            self.generate_btn = ttk.Button(left_panel, text="🔲  Buat QR Code", command=self.buat_qr,
                                           bootstyle="success", padding=(20, 12))
        else:
            self.generate_btn = ttk.Button(left_panel, text="🔲  Buat QR Code", command=self.buat_qr)
        self.generate_btn.pack(fill=X, pady=(5, 5))

        # Action buttons frame
        action_frame = ttk.Frame(left_panel)
        action_frame.pack(fill=X, pady=(0, 5))

        if HAS_TTKBOOTSTRAP:
            self.save_btn = ttk.Button(action_frame, text="💾 Simpan", command=self.save_and_send_qr,
                                       bootstyle="info", padding=(10, 8), state=DISABLED)
            self.telegram_btn = ttk.Button(action_frame, text="📨 Telegram", command=self.open_telegram_settings,
                                           bootstyle="primary-outline", padding=(10, 8))
        else:
            self.save_btn = ttk.Button(action_frame, text="💾 Simpan", command=self.save_and_send_qr, state=DISABLED)
            self.telegram_btn = ttk.Button(action_frame, text="📨 Telegram", command=self.open_telegram_settings)

        self.save_btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 4))
        self.telegram_btn.pack(side=RIGHT, expand=True, fill=X)

        # ── Right Panel (Preview) ──
        right_panel = ttk.Labelframe(main_frame, text="  📷 Preview QR Code  ", padding=15)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True)

        # Center the preview
        preview_container = ttk.Frame(right_panel)
        preview_container.pack(expand=True)

        self.canvas_qr = tk.Canvas(preview_container, width=380, height=380, bg='#F0F0F0',
                                    bd=0, highlightthickness=1, highlightbackground="#CCCCCC")
        self.canvas_qr.pack(pady=10)

        # Placeholder text
        self.canvas_qr.create_text(190, 190, text="QR Code akan muncul\ndi sini",
                                    font=("Segoe UI", 13), fill="#AAAAAA", justify="center", tags="placeholder")

        # Info label
        self.info_label = ttk.Label(preview_container, text="", font=("Segoe UI", 9), foreground="gray", wraplength=350, justify="center")
        self.info_label.pack(pady=(0, 5))

        # ── Status Bar ──
        status_frame = ttk.Frame(self.root, padding=(10, 5))
        status_frame.pack(side=BOTTOM, fill=X)

        self.status_var = tk.StringVar()
        self.status_var.set("✅ Siap — Masukkan URL dan logo untuk membuat QR Code")
        self.status_bar = ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 9))
        self.status_bar.pack(side=LEFT)

        # Telegram status indicator
        tele_status = "🟢 Telegram aktif" if (self.telegram_token and self.telegram_chat_id) else "⚪ Telegram belum diatur"
        self.tele_indicator = ttk.Label(status_frame, text=tele_status, font=("Segoe UI", 9), foreground="gray")
        self.tele_indicator.pack(side=RIGHT)

    # ─── Event handlers ───────────────────────────────────────────
    def _on_history_select(self, event):
        selected = self.history_combo.get()
        if selected:
            self.url_entry.delete(0, END)
            self.url_entry.insert(0, selected)

    def pick_local_image(self):
        filepath = filedialog.askopenfilename(
            title="Pilih Gambar Logo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico"), ("All Files", "*.*")]
        )
        if filepath:
            self.local_image_path = filepath
            basename = os.path.basename(filepath)
            self.local_file_label.config(text=f"📎 {basename}", foreground="#2196F3")
            # Clear the URL entry when local file is selected
            self.img_entry.delete(0, END)

    def clear_local_image(self):
        self.local_image_path = None
        self.local_file_label.config(text="Belum ada file dipilih", foreground="gray")

    def pick_color(self, which):
        initial = self.fg_color if which == "fg" else self.bg_color
        color = colorchooser.askcolor(color=initial, title="Pilih Warna")
        if color[1]:
            if which == "fg":
                self.fg_color = color[1]
                self.fg_canvas.config(bg=self.fg_color)
            else:
                self.bg_color = color[1]
                self.bg_canvas.config(bg=self.bg_color)

    # ─── QR Code Generation ───────────────────────────────────────
    def get_logo_image(self):
        """Get logo from local file or URL."""
        if self.local_image_path and os.path.exists(self.local_image_path):
            return Image.open(self.local_image_path).convert("RGBA")

        image_url = self.img_entry.get().strip()
        if image_url:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGBA")

        return None

    def generate_qr_code_with_image(self, url):
        try:
            self.status_var.set("⏳ Membuat QR Code...")
            self.root.update()

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color=self.fg_color, back_color=self.bg_color).convert('RGB')

            # Try to get logo
            logo = self.get_logo_image()
            if logo:
                self.status_var.set("⏳ Menambahkan logo...")
                self.root.update()

                # Resize logo
                logo_size = int(qr_img.size[0] * 0.25)
                logo = logo.resize((logo_size, logo_size), Resampling.LANCZOS)

                # Create rounded mask for logo
                mask = Image.new("L", (logo_size, logo_size), 0)
                draw = ImageDraw.Draw(mask)
                radius = logo_size // 8
                draw.rounded_rectangle([(0, 0), (logo_size, logo_size)], radius=radius, fill=255)

                # Add white padding behind logo
                padding = 8
                white_bg = Image.new("RGB", (logo_size + padding * 2, logo_size + padding * 2), self.bg_color)

                pos_bg = (
                    (qr_img.size[0] - logo_size - padding * 2) // 2,
                    (qr_img.size[1] - logo_size - padding * 2) // 2
                )
                qr_img.paste(white_bg, pos_bg)

                # Paste logo
                pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
                qr_img.paste(logo, pos, logo)

            self.status_var.set("✅ QR Code berhasil dibuat!")
            return qr_img

        except requests.exceptions.RequestException as e:
            self.status_var.set("❌ Gagal mengambil gambar")
            messagebox.showerror("Error", f"Gagal mengambil gambar logo:\n{e}")
            return None
        except Exception as e:
            self.status_var.set("❌ Error: " + str(e))
            messagebox.showerror("Error", f"Gagal membuat QR Code:\n{e}")
            return None

    def buat_qr(self):
        url = self.url_entry.get().strip()

        if not url or url == "https://":
            messagebox.showwarning("Input Kosong", "Mohon masukkan URL tujuan QR Code!")
            return

        image_url = self.img_entry.get().strip()
        has_local = self.local_image_path and os.path.exists(self.local_image_path)

        if not image_url and not has_local:
            result = messagebox.askyesno("Tanpa Logo",
                                          "Tidak ada logo yang dipilih.\nBuat QR Code tanpa logo?")
            if not result:
                return

        self.qr_image = self.generate_qr_code_with_image(url)

        if self.qr_image:
            # Save to URL history
            self.save_url_history(url)

            # Clear placeholder and show preview
            self.canvas_qr.delete("all")
            preview_size = 380
            self.qr_preview = ImageTk.PhotoImage(self.qr_image.resize((preview_size, preview_size), Resampling.LANCZOS))
            self.canvas_qr.create_image(preview_size // 2, preview_size // 2, anchor="center", image=self.qr_preview)

            # Enable save button
            self.save_btn.config(state=NORMAL)

            # Show info
            size = self.qr_image.size
            self.info_label.config(text=f"Ukuran: {size[0]}×{size[1]}px  |  URL: {url[:50]}{'...' if len(url) > 50 else ''}")

    # ─── Save & Send ──────────────────────────────────────────────
    def save_and_send_qr(self):
        if not self.qr_image:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg"), ("All Files", "*.*")],
            initialfile="qrcode_output"
        )
        if filename:
            self.qr_image.save(filename)
            self.status_var.set(f"✅ QR Code disimpan: {os.path.basename(filename)}")
            messagebox.showinfo("Berhasil", f"QR Code berhasil disimpan di:\n{filename}")

            # Send to Telegram if configured
            if self.telegram_token and self.telegram_chat_id:
                result = messagebox.askyesno("Kirim ke Telegram", "Kirim QR Code ke Telegram?")
                if result:
                    self.status_var.set("📨 Mengirim ke Telegram...")
                    self.root.update()
                    threading.Thread(target=self.send_to_telegram, args=(filename,), daemon=True).start()

    def send_to_telegram(self, file_path):
        try:
            bot = telebot.TeleBot(self.telegram_token)
            with open(file_path, 'rb') as photo:
                bot.send_photo(self.telegram_chat_id, photo, caption=f"🔲 QR Code: {self.url_entry.get()}")
            self.status_var.set("✅ QR Code berhasil dikirim ke Telegram!")
            messagebox.showinfo("Berhasil", "QR Code berhasil dikirim ke Telegram!")
        except Exception as e:
            self.status_var.set("❌ Gagal mengirim ke Telegram")
            messagebox.showerror("Error Telegram", f"Gagal mengirim ke Telegram:\n{e}")

    # ─── Telegram Config ──────────────────────────────────────────
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
        settings_window.title("📨 Pengaturan Telegram")
        settings_window.geometry("450x320")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        frame = ttk.Frame(settings_window, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Pengaturan Bot Telegram", font=("Segoe UI", 14, "bold")).pack(pady=(0, 15))

        # Token field
        ttk.Label(frame, text="Token Bot Telegram:", font=("Segoe UI", 10)).pack(anchor=W, pady=(0, 3))
        token_entry = ttk.Entry(frame, width=50, font=("Segoe UI", 10))
        token_entry.pack(fill=X, pady=(0, 10))
        token_entry.insert(0, self.telegram_token)

        # Chat ID field
        ttk.Label(frame, text="Chat ID Tujuan:", font=("Segoe UI", 10)).pack(anchor=W, pady=(0, 3))
        chat_id_entry = ttk.Entry(frame, width=50, font=("Segoe UI", 10))
        chat_id_entry.pack(fill=X, pady=(0, 15))
        chat_id_entry.insert(0, self.telegram_chat_id)

        def save_settings():
            self.telegram_token = token_entry.get().strip()
            self.telegram_chat_id = chat_id_entry.get().strip()
            self.save_telegram_config()

            tele_status = "🟢 Telegram aktif" if (self.telegram_token and self.telegram_chat_id) else "⚪ Telegram belum diatur"
            self.tele_indicator.config(text=tele_status)

            messagebox.showinfo("Berhasil", "Pengaturan Telegram berhasil disimpan!")
            settings_window.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, pady=(5, 0))

        if HAS_TTKBOOTSTRAP:
            save_button = ttk.Button(btn_frame, text="💾 Simpan Pengaturan", command=save_settings,
                                     bootstyle="success", padding=(15, 10))
            help_button = ttk.Button(btn_frame, text="❓ Panduan", bootstyle="info-outline", padding=(15, 10),
                                     command=lambda: messagebox.showinfo(
                                         "Panduan Telegram",
                                         "📌 Cara mendapatkan Token Bot:\n"
                                         "1. Chat @BotFather di Telegram\n"
                                         "2. Kirim /newbot\n"
                                         "3. Salin token yang diberikan\n\n"
                                         "📌 Cara mendapatkan Chat ID:\n"
                                         "1. Chat @userinfobot di Telegram\n"
                                         "2. Salin ID yang diberikan"))
        else:
            save_button = ttk.Button(btn_frame, text="💾 Simpan Pengaturan", command=save_settings)
            help_button = ttk.Button(btn_frame, text="❓ Panduan",
                                     command=lambda: messagebox.showinfo(
                                         "Panduan Telegram",
                                         "📌 Cara mendapatkan Token Bot:\n"
                                         "1. Chat @BotFather di Telegram\n"
                                         "2. Kirim /newbot\n"
                                         "3. Salin token yang diberikan\n\n"
                                         "📌 Cara mendapatkan Chat ID:\n"
                                         "1. Chat @userinfobot di Telegram\n"
                                         "2. Salin ID yang diberikan"))

        save_button.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        help_button.pack(side=RIGHT, expand=True, fill=X)


if __name__ == "__main__":
    if HAS_TTKBOOTSTRAP:
        root = ttk.Window(
            title="QR Code Generator",
            themename="darkly",
            size=(820, 620),
            minsize=(820, 620),
        )
    else:
        root = tk.Tk()
        root.title("QR Code Generator")
        root.geometry("820x620")
        root.minsize(820, 620)

    app = QRCodeGenerator(root)
    root.mainloop()