import qrcode
from PIL import Image, ImageTk
from PIL.Image import Resampling  # FIX untuk PIL >= 10
import requests
from io import BytesIO
import tkinter as tk
from tkinter import messagebox, filedialog

def generate_qr_code_with_image_gui(url, image_url):
    try:
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
        logo_size = int(qr_img.size[0] * 0.2)
        logo = logo.resize((logo_size, logo_size), Resampling.LANCZOS)  # ✅ Ganti ANTIALIAS

        # Tempel logo ke tengah QR code
        pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
        qr_img.paste(logo, pos, logo)

        return qr_img

    except Exception as e:
        messagebox.showerror("Error", f"Gagal membuat QR Code:\n{e}")
        return None

def buat_qr():
    url = url_entry.get().strip()
    image_url = img_entry.get().strip()

    if not url or not image_url:
        messagebox.showwarning("Input Kosong", "Mohon masukkan URL dan URL Gambar!")
        return

    qr_image = generate_qr_code_with_image_gui(url, image_url)

    if qr_image:
        # Tampilkan preview di canvas
        global qr_preview
        qr_preview = ImageTk.PhotoImage(qr_image.resize((250, 250)))
        canvas_qr.create_image(0, 0, anchor="nw", image=qr_preview)

        # Simpan QR code ke file
        def save_file():
            filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
            if filename:
                qr_image.save(filename)
                messagebox.showinfo("Berhasil", f"QR Code berhasil disimpan di:\n{filename}")

        save_btn.config(command=save_file)
        save_btn.pack(pady=5)

# ==== GUI Setup ====
root = tk.Tk()
root.title("QR Code Generator dengan Gambar di Tengah")
root.geometry("400x500")
root.resizable(False, False)

# Input URL
tk.Label(root, text="Masukkan URL tujuan QR Code:").pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

# Input Gambar
tk.Label(root, text="Masukkan URL Gambar (misal: link GitHub raw):").pack(pady=5)
img_entry = tk.Entry(root, width=50)
img_entry.pack(pady=5)

# Tombol Generate
generate_btn = tk.Button(root, text="Buat QR Code", command=buat_qr, bg="green", fg="white")
generate_btn.pack(pady=10)

# Canvas untuk menampilkan hasil
canvas_qr = tk.Canvas(root, width=250, height=250, bg='white')
canvas_qr.pack(pady=10)

# Tombol Simpan (ditampilkan setelah QR dibuat)
save_btn = tk.Button(root, text="Simpan QR Code", bg="blue", fg="white")

root.mainloop()
