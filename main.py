

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os

import enkripsi  # Modul logika enkripsi
import dekripsi  # Modul logika dekripsi
from img_load import load_and_prepare  # Untuk preview gambar


# ─── Warna & Font ─────────────────────────────────────────────────────────────

C_BG        = '#FFFFFF'   # Background utama (gelap)
C_SURFACE   = '#FFFFFF'   # Background panel/frame
C_ENCRYPT   = '#7C3AED'   # Ungu (enkripsi)
C_ENCRYPT_H = '#6D28D9'   # Ungu hover
C_DECRYPT   = '#059669'   # Hijau (dekripsi)
C_DECRYPT_H = '#047857'   # Hijau hover
C_TEXT      = '#000000'   # Teks utama
C_SUBTEXT   = '#000000'   # Teks sekunder
C_BORDER    = '#000000'   # Border

FONT_TITLE  = ('Segoe UI', 22, 'bold')
FONT_HEAD   = ('Segoe UI', 13, 'bold')
FONT_BODY   = ('Segoe UI', 10)
FONT_SMALL  = ('Segoe UI', 8)
FONT_BTN    = ('Segoe UI', 10, 'bold')


def _style_btn(btn, color, hover_color):
    btn.config(bg=color, fg='white', relief='flat', cursor='hand2',
               activebackground=hover_color, activeforeground='white',
               bd=0, padx=16, pady=8, font=FONT_BTN)
    btn.bind('<Enter>', lambda e: btn.config(bg=hover_color))
    btn.bind('<Leave>', lambda e: btn.config(bg=color))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

class MainMenu:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('StegoCrypt — AES-CBC + EOF Steganografi')
        root.geometry('420x380')
        root.resizable(False, False)
        root.configure(bg=C_BG)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=C_BG)
        hdr.pack(pady=(36, 8))

        tk.Label(hdr, text='🔐 StegoCrypt', font=FONT_TITLE,
                 bg=C_BG, fg=C_TEXT).pack()
        tk.Label(hdr, text='Enkripsi & Steganografi Gambar — AES-256-CBC + EOF',
                 font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(pady=4)

        # ── Separator ───────────────────────────────────────────────────────
        tk.Frame(root, bg=C_BORDER, height=1).pack(fill='x', padx=30, pady=12)

        # ── Tombol menu ─────────────────────────────────────────────────────
        card = tk.Frame(root, bg=C_SURFACE, bd=0, relief='flat')
        card.pack(padx=40, pady=8, fill='x')

        inner = tk.Frame(card, bg=C_SURFACE)
        inner.pack(padx=20, pady=20)

        tk.Label(inner, text='Pilih Operasi', font=FONT_HEAD,
                 bg=C_SURFACE, fg=C_TEXT).pack(pady=(0, 16))

        btn_enc = tk.Button(inner, text='🔒  Enkripsi Gambar',
                            width=28, command=self.open_encrypt)
        _style_btn(btn_enc, C_ENCRYPT, C_ENCRYPT_H)
        btn_enc.pack(pady=6, ipady=2)

        btn_dec = tk.Button(inner, text='🔓  Dekripsi Gambar',
                            width=28, command=self.open_decrypt)
        _style_btn(btn_dec, C_DECRYPT, C_DECRYPT_H)
        btn_dec.pack(pady=6, ipady=2)

        # ── Footer ──────────────────────────────────────────────────────────
        tk.Label(root, text='AES-256-CBC  ·  PBKDF2-SHA256  ·  EOF Steganografi',
                 font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(side='bottom', pady=5)

    def open_encrypt(self):
        self.root.withdraw()
        win = tk.Toplevel(self.root)
        EncryptWindow(win, self.root)

    def open_decrypt(self):
        self.root.withdraw()
        win = tk.Toplevel(self.root)
        DecryptWindow(win, self.root)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENKRIPSI WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptWindow:
    PREV_SIZE = 300  # Ukuran masing-masing canvas preview

    def __init__(self, window: tk.Toplevel, parent: tk.Tk):
        self.window      = window
        self.parent      = parent
        self.src_path    = None   # Path gambar yang akan dienkripsi
        self.cover_path  = None   # Path gambar cover (host EOF)
        self.password    = None   # Password enkripsi
        self.photo_src   = None   # Referensi ImageTk sumber (agar tidak di-GC)
        self.photo_cover = None   # Referensi ImageTk cover

        window.title('StegoCrypt — Enkripsi Gambar')
        window.geometry('760x720')
        window.resizable(False, False)
        window.configure(bg=C_BG)
        window.protocol('WM_DELETE_WINDOW', self._on_close)

        self._build_ui()

    def _build_ui(self):
        w = self.window

        # ── Header strip ────────────────────────────────────────────────────────
        hdr = tk.Frame(w, bg=C_ENCRYPT, height=44)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='🔒  Enkripsi Gambar', font=FONT_HEAD,
                 bg=C_ENCRYPT, fg='white').pack(side='left', padx=16, pady=10)

        # ── Baris tombol ────────────────────────────────────────────────────────
        btn_row = tk.Frame(w, bg=C_BG)
        btn_row.pack(pady=12)

        btn_src = tk.Button(btn_row, text='🖼  Pilih Gambar Asli',
                            command=self._load_src, width=20)
        _style_btn(btn_src, C_ENCRYPT, C_ENCRYPT_H)
        btn_src.pack(side='left', padx=6)

        btn_cov = tk.Button(btn_row, text='🎨  Pilih Gambar Cover',
                            command=self._load_cover, width=20)
        _style_btn(btn_cov, '#0F766E', '#0D6B63')
        btn_cov.pack(side='left', padx=6)

        btn_pwd = tk.Button(btn_row, text='🔑  Password',
                            command=self._ask_password, width=14)
        _style_btn(btn_pwd, '#4F46E5', '#4338CA')
        btn_pwd.pack(side='left', padx=6)

        # ── Dua canvas preview side-by-side ─────────────────────────────────────
        previews = tk.Frame(w, bg=C_BG)
        previews.pack(pady=4, padx=16)

        # Panel gambar asli (sumber)
        left = tk.Frame(previews, bg=C_BG)
        left.pack(side='left', padx=8)

        tk.Label(left, text='Gambar yang Dienkripsi', font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(pady=(0, 4))

        src_border = tk.Frame(left, bg=C_ENCRYPT, bd=2, relief='flat')
        src_border.pack()
        self.canvas_src = tk.Canvas(src_border, width=self.PREV_SIZE,
                                    height=self.PREV_SIZE, bg=C_SURFACE,
                                    highlightthickness=0)
        self.canvas_src.pack()
        self.canvas_src.create_text(
            self.PREV_SIZE // 2, self.PREV_SIZE // 2,
            text='Pilih gambar asli\n🖼',
            fill=C_SUBTEXT, font=FONT_BODY, tags='ph_src', justify='center')

        self.lbl_src_info = tk.Label(left, text='—', font=FONT_SMALL,
                                     bg=C_BG, fg=C_SUBTEXT, wraplength=300)
        self.lbl_src_info.pack(pady=(4, 0))

        # Panel gambar cover
        right = tk.Frame(previews, bg=C_BG)
        right.pack(side='left', padx=8)

        tk.Label(right, text='Gambar Cover (Host)', font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(pady=(0, 4))

        cov_border = tk.Frame(right, bg='#0F766E', bd=2, relief='flat')
        cov_border.pack()
        self.canvas_cov = tk.Canvas(cov_border, width=self.PREV_SIZE,
                                    height=self.PREV_SIZE, bg=C_SURFACE,
                                    highlightthickness=0)
        self.canvas_cov.pack()
        self.canvas_cov.create_text(
            self.PREV_SIZE // 2, self.PREV_SIZE // 2,
            text='Pilih gambar cover\n🎨\n(opsional — jika kosong\npakai gambar asli)',
            fill=C_SUBTEXT, font=FONT_BODY, tags='ph_cov', justify='center')

        self.lbl_cov_info = tk.Label(right, text='—', font=FONT_SMALL,
                                     bg=C_BG, fg=C_SUBTEXT, wraplength=300)
        self.lbl_cov_info.pack(pady=(4, 0))

        # ── Info password & status ───────────────────────────────────────────────
        info = tk.Frame(w, bg=C_SURFACE)
        info.pack(fill='x', padx=16, pady=6)

        self.lbl_pass = tk.Label(info, text='Password: belum dimasukkan',
                                 font=FONT_SMALL, bg=C_SURFACE, fg=C_SUBTEXT, anchor='w')
        self.lbl_pass.pack(fill='x', padx=12, pady=6)

        # ── Tombol enkripsi ──────────────────────────────────────────────────────
        btn_enc = tk.Button(w, text='💾  Simpan & Enkripsi',
                            command=self._encrypt, width=30)
        _style_btn(btn_enc, C_ENCRYPT, C_ENCRYPT_H)
        btn_enc.pack(pady=8, ipady=4)

        btn_back = tk.Button(w, text='← Kembali', command=self._on_close,
                             bg=C_SURFACE, fg=C_SUBTEXT, relief='flat',
                             font=FONT_BODY, cursor='hand2',
                             activebackground=C_BORDER, activeforeground=C_TEXT)
        btn_back.pack(pady=2)

        self.lbl_status = tk.Label(w, text='Pilih gambar asli dan (opsional) gambar cover, lalu masukkan password.',
                                   font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT)
        self.lbl_status.pack(side='bottom', pady=6)

    # ── Handler ───────────────────────────────────────────────────────────────

    def _load_src(self):
        path = filedialog.askopenfilename(
            title='Pilih Gambar yang Akan Dienkripsi',
            filetypes=[('Gambar', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff'), ('Semua', '*.*')]
        )
        if not path:
            return
        try:
            pil_img, _, mode, channels = load_and_prepare(path)
            self.src_path = path
            self._show_preview(self.canvas_src, pil_img, 'ph_src', 'photo_src')
            ext = os.path.splitext(path)[1].lower()
            self.lbl_src_info.config(
                text=f'{os.path.basename(path)}  [{ext}]  |  {mode}  {channels}ch  512×512',
                fg=C_TEXT)
            self._status(f'Gambar asli dipilih: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('Gagal Memuat Gambar', str(e), parent=self.window)

    def _load_cover(self):
        path = filedialog.askopenfilename(
            title='Pilih Gambar Cover (Host)',
            filetypes=[('Gambar', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff'), ('Semua', '*.*')]
        )
        if not path:
            return
        try:
            pil_img, _, mode, channels = load_and_prepare(path)
            self.cover_path = path
            self._show_preview(self.canvas_cov, pil_img, 'ph_cov', 'photo_cover')
            ext = os.path.splitext(path)[1].lower()
            self.lbl_cov_info.config(
                text=f'{os.path.basename(path)}  [{ext}]  |  {mode}  {channels}ch  512×512',
                fg='#34D399')
            self._status(f'Gambar cover dipilih: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('Gagal Memuat Cover', str(e), parent=self.window)

    def _ask_password(self):
        pwd = simpledialog.askstring('Password Enkripsi',
                                     'Masukkan password untuk enkripsi:',
                                     show='*', parent=self.window)
        if pwd is None:
            return
        if not pwd.strip():
            messagebox.showwarning('Password Kosong', 'Password tidak boleh kosong!',
                                   parent=self.window)
            return
        self.password = pwd
        self.lbl_pass.config(text='Password: ✔ sudah dimasukkan', fg='#34D399')
        self._status('Password sudah diatur.')

    def _show_preview(self, canvas, pil_img, placeholder_tag, photo_attr):
        canvas.delete(placeholder_tag)
        preview = pil_img.resize((self.PREV_SIZE, self.PREV_SIZE), Image.LANCZOS)
        if preview.mode == 'L':
            preview = preview.convert('RGB')
        photo = ImageTk.PhotoImage(preview)
        setattr(self, photo_attr, photo)   # simpan referensi agar tidak di-GC
        canvas.create_image(0, 0, anchor='nw', image=photo)

    def _encrypt(self):
        if not self.src_path:
            messagebox.showwarning('Peringatan', 'Pilih gambar asli terlebih dahulu!',
                                   parent=self.window)
            return
        if not self.password:
            messagebox.showwarning('Peringatan', 'Masukkan password terlebih dahulu!',
                                   parent=self.window)
            return

        # Extension output mengikuti cover (jika ada) atau sumber
        host = self.cover_path if self.cover_path else self.src_path
        ext  = os.path.splitext(host)[1].lower()
        fmt_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG',
                   '.bmp': 'BMP', '.tif': 'TIFF', '.tiff': 'TIFF'}
        label = fmt_map.get(ext, 'Gambar')

        out = filedialog.asksaveasfilename(
            title='Simpan Gambar Terenkripsi',
            defaultextension=ext,
            initialfile=f'enkripsi{ext}',
            filetypes=[(f'{label} files', f'*{ext}'), ('Semua file', '*.*')]
        )
        if not out:
            return

        self._status('Memproses enkripsi... harap tunggu.')
        self.window.update()

        result = enkripsi.encrypt_image(
            self.src_path, out, self.password,
            cover_path=self.cover_path   # None = pakai gambar asli sebagai cover
        )

        if result['success']:
            cover_note = f'\nCover  : {os.path.basename(self.cover_path)}' if self.cover_path else ''
            messagebox.showinfo(
                'Enkripsi Berhasil',
                f'Gambar berhasil dienkripsi!\n\n'
                f'Mode   : {result["mode"]}{cover_note}\n'
                f'Output : {result["output"]}',
                parent=self.window
            )
            self._status('Enkripsi selesai. ✔')
        else:
            messagebox.showerror('Enkripsi Gagal',
                                 f'Gagal mengenkripsi gambar:\n\n{result["error"]}',
                                 parent=self.window)
            self._status('Enkripsi gagal.')

    def _status(self, msg: str):
        self.lbl_status.config(text=msg)

    def _on_close(self):
        self.window.destroy()
        self.parent.deiconify()


# ═══════════════════════════════════════════════════════════════════════════════
#  DEKRIPSI WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class DecryptWindow:
    CANVAS_SIZE = 512

    def __init__(self, window: tk.Toplevel, parent: tk.Tk):
        self.window    = window
        self.parent    = parent
        self.stego_path = None  # Path file gambar stego (terenkripsi)
        self.password  = None   # Password dekripsi
        self.photo     = None   # Referensi ImageTk

        window.title('StegoCrypt — Dekripsi Gambar')
        window.geometry('620x760')
        window.resizable(False, False)
        window.configure(bg=C_BG)
        window.protocol('WM_DELETE_WINDOW', self._on_close)

        self._build_ui()

    def _build_ui(self):
        w = self.window

        # Header strip
        hdr = tk.Frame(w, bg=C_DECRYPT, height=44)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='🔓  Dekripsi Gambar', font=FONT_HEAD,
                 bg=C_DECRYPT, fg='white').pack(side='left', padx=16, pady=10)

        # Tombol aksi
        btn_row = tk.Frame(w, bg=C_BG)
        btn_row.pack(pady=14)

        btn_img = tk.Button(btn_row, text='📂  Pilih Gambar Stego',
                            command=self._load_image, width=20)
        _style_btn(btn_img, C_DECRYPT, C_DECRYPT_H)
        btn_img.pack(side='left', padx=8)

        btn_pwd = tk.Button(btn_row, text='🔑  Masukkan Password',
                            command=self._ask_password, width=20)
        _style_btn(btn_pwd, '#0F766E', '#0D6B63')
        btn_pwd.pack(side='left', padx=8)

        # Canvas preview
        canvas_frame = tk.Frame(w, bg=C_BORDER, bd=1)
        canvas_frame.pack(pady=4)
        self.canvas = tk.Canvas(canvas_frame, width=self.CANVAS_SIZE,
                                height=self.CANVAS_SIZE, bg=C_SURFACE,
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_text(self.CANVAS_SIZE // 2, self.CANVAS_SIZE // 2,
                                text='Preview gambar stego akan muncul di sini',
                                fill=C_SUBTEXT, font=FONT_BODY, tags='placeholder')

        # Info panel
        info = tk.Frame(w, bg=C_SURFACE)
        info.pack(fill='x', padx=16, pady=6)

        self.lbl_file = tk.Label(info, text='File   : —', font=FONT_SMALL,
                                 bg=C_SURFACE, fg=C_SUBTEXT, anchor='w')
        self.lbl_file.pack(fill='x', padx=12, pady=(8, 0))

        self.lbl_eof = tk.Label(info, text='Data EOF : —', font=FONT_SMALL,
                                bg=C_SURFACE, fg=C_SUBTEXT, anchor='w')
        self.lbl_eof.pack(fill='x', padx=12)

        self.lbl_pass = tk.Label(info, text='Password : belum dimasukkan',
                                 font=FONT_SMALL, bg=C_SURFACE, fg=C_SUBTEXT, anchor='w')
        self.lbl_pass.pack(fill='x', padx=12, pady=(0, 8))

        # Tombol dekripsi
        btn_dec = tk.Button(w, text='💾  Simpan & Dekripsi',
                            command=self._decrypt, width=30)
        _style_btn(btn_dec, C_DECRYPT, C_DECRYPT_H)
        btn_dec.pack(pady=8, ipady=4)

        # Tombol kembali
        btn_back = tk.Button(w, text='← Kembali', command=self._on_close,
                             bg=C_SURFACE, fg=C_SUBTEXT, relief='flat',
                             font=FONT_BODY, cursor='hand2',
                             activebackground=C_BORDER, activeforeground=C_TEXT)
        btn_back.pack(pady=2)

        # Status bar
        self.lbl_status = tk.Label(w, text='Silakan pilih gambar stego dan masukkan password.',
                                   font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT)
        self.lbl_status.pack(side='bottom', pady=6)

    # ── Handler ───────────────────────────────────────────────────────────────

    def _load_image(self):
        from eof import has_eof_data

        path = filedialog.askopenfilename(
            title='Pilih Gambar Terenkripsi (Stego)',
            filetypes=[('Gambar', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff'), ('Semua', '*.*')]
        )
        if not path:
            return

        try:
            pil_img, arr, mode, channels = load_and_prepare(path)
            self.stego_path = path
            self._show_preview(pil_img)

            # Cek apakah file memiliki data EOF
            has_data = has_eof_data(path)
            eof_status = '✔ Terdeteksi data tersembunyi' if has_data else '✘ Tidak ada data EOF'
            eof_color  = '#34D399' if has_data else '#F87171'

            self.lbl_file.config(text=f'File   : {os.path.basename(path)}')
            self.lbl_eof.config(text=f'Data EOF : {eof_status}', fg=eof_color)
            self._status(f'Gambar dipilih: {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('Gagal Memuat Gambar', str(e), parent=self.window)

    def _ask_password(self):
        pwd = simpledialog.askstring('Password Dekripsi',
                                     'Masukkan password untuk dekripsi:',
                                     show='*', parent=self.window)
        if pwd is None:
            return
        if not pwd.strip():
            messagebox.showwarning('Password Kosong', 'Password tidak boleh kosong!',
                                   parent=self.window)
            return
        self.password = pwd
        self.lbl_pass.config(text='Password : ✔ sudah dimasukkan', fg='#34D399')
        self._status('Password sudah diatur.')

    def _show_preview(self, pil_img):
        self.canvas.delete('placeholder')
        preview = pil_img.resize((self.CANVAS_SIZE, self.CANVAS_SIZE), Image.LANCZOS)
        if preview.mode == 'L':
            preview = preview.convert('RGB')
        self.photo = ImageTk.PhotoImage(preview)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def _decrypt(self):
        if not self.stego_path:
            messagebox.showwarning('Peringatan', 'Pilih gambar stego terlebih dahulu!',
                                   parent=self.window)
            return
        if not self.password:
            messagebox.showwarning('Peringatan', 'Masukkan password terlebih dahulu!',
                                   parent=self.window)
            return

        out = filedialog.asksaveasfilename(
            title='Simpan Gambar Hasil Dekripsi',
            defaultextension='.png',
            initialfile='dekripsi',
            filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg'), ('BMP', '*.bmp'),
                       ('TIFF', '*.tiff'), ('Semua', '*.*')]
        )
        if not out:
            return

        self._status('Memproses dekripsi... harap tunggu.')
        self.window.update()

        result = dekripsi.decrypt_image(self.stego_path, out, self.password)

        if result['success']:
            messagebox.showinfo(
                'Dekripsi Berhasil',
                f'Gambar berhasil didekripsi!\n\n'
                f'Format asli : {result["original_format"]}\n'
                f'Mode        : {result["mode"]}\n'
                f'Output      : {result["output"]}',
                parent=self.window
            )
            self._status('Dekripsi selesai. ✔')
        else:
            messagebox.showerror('Dekripsi Gagal',
                                 f'{result["error"]}',
                                 parent=self.window)
            self._status('Dekripsi gagal.')

    def _status(self, msg: str):
        self.lbl_status.config(text=msg)

    def _on_close(self):
        self.window.destroy()
        self.parent.deiconify()


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()
