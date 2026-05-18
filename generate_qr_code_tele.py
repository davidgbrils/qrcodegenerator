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
import zipfile

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
        self.root.geometry("980x680")
        self.root.minsize(980, 680)
        self.qr_image = None
        self.qr_preview = None
        self.generated_qrs = []
        self.qr_previews = []
        self.qr_inputs = []
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

        # URL Inputs
        ttk.Label(left_panel, text="URL Tujuan QR Code:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        for index in range(3):
            row_frame = ttk.Frame(left_panel)
            row_frame.pack(fill=X, pady=(0, 5))

            url_frame = ttk.Frame(row_frame)
            url_frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
            ttk.Label(url_frame, text=f"Link {index + 1}", font=("Segoe UI", 8)).pack(anchor=W)
            url_entry = ttk.Entry(url_frame, width=24, font=("Segoe UI", 9))
            url_entry.pack(fill=X)
            if index == 0:
                url_entry.insert(0, "https://")

            name_frame = ttk.Frame(row_frame)
            name_frame.pack(side=RIGHT, fill=X, expand=False)
            ttk.Label(name_frame, text="Nama file", font=("Segoe UI", 8)).pack(anchor=W)
            name_entry = ttk.Entry(name_frame, width=14, font=("Segoe UI", 9))
            name_entry.pack(fill=X)
            name_entry.insert(0, f"qrcode_{index + 1}")

            self.qr_inputs.append({"url": url_entry, "name": name_entry})

        self.url_entry = self.qr_inputs[0]["url"]

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
            self.save_btn = ttk.Button(action_frame, text="💾 Export ZIP", command=self.save_and_send_qr,
                                       bootstyle="info", padding=(10, 8), state=DISABLED)
            self.telegram_btn = ttk.Button(action_frame, text="📨 Telegram", command=self.open_telegram_settings,
                                           bootstyle="primary-outline", padding=(10, 8))
        else:
            self.save_btn = ttk.Button(action_frame, text="💾 Export ZIP", command=self.save_and_send_qr, state=DISABLED)
            self.telegram_btn = ttk.Button(action_frame, text="📨 Telegram", command=self.open_telegram_settings)

        self.save_btn.pack(side=LEFT, expand=True, fill=X, padx=(0, 4))
        self.telegram_btn.pack(side=RIGHT, expand=True, fill=X)

        # ── Right Panel (Preview) ──
        right_panel = ttk.Labelframe(main_frame, text="  📷 Preview QR Code  ", padding=15)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True)

        # Center the preview
        preview_container = ttk.Frame(right_panel)
        preview_container.pack(expand=True)

        preview_grid = ttk.Frame(preview_container)
        preview_grid.pack(pady=10)

        self.canvas_qr = None
        self.preview_canvases = []
        for index in range(3):
            card = ttk.Frame(preview_grid)
            card.grid(row=0, column=index, padx=6, sticky=N)
            ttk.Label(card, text=f"QR {index + 1}", font=("Segoe UI", 9, "bold")).pack(anchor=W)
            canvas = tk.Canvas(card, width=180, height=180, bg='#F0F0F0',
                               bd=0, highlightthickness=1, highlightbackground="#CCCCCC")
            canvas.pack()
            canvas.create_text(90, 90, text="Belum dibuat",
                               font=("Segoe UI", 10), fill="#AAAAAA", justify="center", tags="placeholder")
            self.preview_canvases.append(canvas)

        self.canvas_qr = self.preview_canvases[0]

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
            self.qr_inputs[0]["url"].delete(0, END)
            self.qr_inputs[0]["url"].insert(0, selected)

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

    def sanitize_filename(self, filename, fallback):
        safe_name = "".join(
            char if char.isalnum() or char in (" ", "-", "_") else "_"
            for char in filename.strip()
        ).strip()
        safe_name = "_".join(safe_name.split())
        return safe_name or fallback

    def collect_qr_requests(self):
        requests_data = []
        used_names = set()

        for index, fields in enumerate(self.qr_inputs, start=1):
            url = fields["url"].get().strip()
            raw_name = fields["name"].get().strip()

            if not url or url == "https://":
                continue

            filename = self.sanitize_filename(raw_name, f"qrcode_{index}")
            base_filename = filename
            counter = 2
            while filename.lower() in used_names:
                filename = f"{base_filename}_{counter}"
                counter += 1

            used_names.add(filename.lower())
            requests_data.append({
                "url": url,
                "filename": filename,
                "label": raw_name or filename,
            })

        return requests_data

    def clear_previews(self):
        self.qr_previews = []
        for index, canvas in enumerate(self.preview_canvases, start=1):
            canvas.delete("all")
            canvas.create_text(90, 90, text="Belum dibuat",
                               font=("Segoe UI", 10), fill="#AAAAAA", justify="center", tags="placeholder")

    def update_previews(self):
        self.qr_previews = []
        for index, canvas in enumerate(self.preview_canvases):
            canvas.delete("all")
            if index < len(self.generated_qrs):
                qr_data = self.generated_qrs[index]
                preview = ImageTk.PhotoImage(qr_data["image"].resize((180, 180), Resampling.LANCZOS))
                self.qr_previews.append(preview)
                canvas.create_image(90, 90, anchor="center", image=preview)
            else:
                canvas.create_text(90, 90, text="Belum dibuat",
                                   font=("Segoe UI", 10), fill="#AAAAAA", justify="center", tags="placeholder")

    def buat_qr(self):
        qr_requests = self.collect_qr_requests()

        if not qr_requests:
            messagebox.showwarning("Input Kosong", "Mohon masukkan minimal 1 URL tujuan QR Code!")
            return

        image_url = self.img_entry.get().strip()
        has_local = self.local_image_path and os.path.exists(self.local_image_path)

        if not image_url and not has_local:
            result = messagebox.askyesno("Tanpa Logo",
                                          "Tidak ada logo yang dipilih.\nBuat QR Code tanpa logo?")
            if not result:
                return

        self.generated_qrs = []
        self.clear_previews()

        for index, qr_request in enumerate(qr_requests, start=1):
            self.status_var.set(f"⏳ Membuat QR Code {index}/{len(qr_requests)}...")
            self.root.update()

            qr_image = self.generate_qr_code_with_image(qr_request["url"])
            if not qr_image:
                return

            self.generated_qrs.append({
                "url": qr_request["url"],
                "filename": qr_request["filename"],
                "image": qr_image,
            })
            self.save_url_history(qr_request["url"])

        if self.generated_qrs:
            self.qr_image = self.generated_qrs[0]["image"]
            self.update_previews()
            self.save_btn.config(state=NORMAL)

            total = len(self.generated_qrs)
            filenames = ", ".join(f"{item['filename']}.png" for item in self.generated_qrs)
            self.info_label.config(text=f"{total} QR Code siap diexport ZIP: {filenames}")
            self.status_var.set(f"✅ {total} QR Code berhasil dibuat!")

    # ─── Save & Send ──────────────────────────────────────────────
    def save_and_send_qr(self):
        if not self.generated_qrs:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")],
            initialfile="qrcode_export.zip"
        )
        if filename:
            with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                for item in self.generated_qrs:
                    image_buffer = BytesIO()
                    item["image"].save(image_buffer, format="PNG")
                    zip_file.writestr(f"{item['filename']}.png", image_buffer.getvalue())

            self.status_var.set(f"✅ ZIP disimpan: {os.path.basename(filename)}")
            messagebox.showinfo("Berhasil", f"ZIP QR Code berhasil disimpan di:\n{filename}")

            # Send to Telegram if configured
            if self.telegram_token and self.telegram_chat_id:
                result = messagebox.askyesno("Kirim ke Telegram", "Kirim ZIP QR Code ke Telegram?")
                if result:
                    self.status_var.set("📨 Mengirim ke Telegram...")
                    self.root.update()
                    threading.Thread(target=self.send_to_telegram, args=(filename,), daemon=True).start()

    def send_to_telegram(self, file_path):
        try:
            bot = telebot.TeleBot(self.telegram_token)
            caption = f"🔲 Export {len(self.generated_qrs)} QR Code"
            with open(file_path, 'rb') as document:
                bot.send_document(self.telegram_chat_id, document, caption=caption)
            self.status_var.set("✅ ZIP QR Code berhasil dikirim ke Telegram!")
            messagebox.showinfo("Berhasil", "ZIP QR Code berhasil dikirim ke Telegram!")
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
            size=(980, 680),
            minsize=(980, 680),
        )
    else:
        root = tk.Tk()
        root.title("QR Code Generator")
        root.geometry("980x680")
        root.minsize(980, 680)

    app = QRCodeGenerator(root)
    root.mainloop()
