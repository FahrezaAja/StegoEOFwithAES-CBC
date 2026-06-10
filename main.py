import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import numpy as np
from image_load import load_image, save_array_as_image, to_grayscale, to_rgb
import encryp, decryp


class MainMenu:
    """Menu utama untuk memilih Enkripsi atau Dekripsi"""
    def __init__(self, root):
        self.root = root
        root.title('StegoCrypt - Main Menu')
        root.geometry('400x300')
        root.resizable(False, False)
        
        frame = tk.Frame(root)
        frame.pack(expand=True)
        
        title = tk.Label(frame, text='StegoCrypt', font=('Arial', 24, 'bold'))
        title.pack(pady=20)
        
        subtitle = tk.Label(frame, text='Pilih Operasi:', font=('Arial', 12))
        subtitle.pack(pady=10)
        
        btn_encrypt = tk.Button(frame, text='Enkripsi Gambar', command=self.open_encrypt, 
                                width=20, height=3, font=('Arial', 11), bg='#6C5CE7', fg='white')
        btn_encrypt.pack(pady=10)
        
        btn_decrypt = tk.Button(frame, text='Dekripsi Gambar', command=self.open_decrypt, 
                                width=20, height=3, font=('Arial', 11), bg='#00B894', fg='white')
        btn_decrypt.pack(pady=10)
    
    def open_encrypt(self):
        self.root.withdraw()
        encrypt_window = tk.Toplevel(self.root)
        EncryptWindow(encrypt_window, self.root)
    
    def open_decrypt(self):
        self.root.withdraw()
        decrypt_window = tk.Toplevel(self.root)
        DecryptWindow(decrypt_window, self.root)


class EncryptWindow:
    """Window untuk proses enkripsi"""
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.window.title('StegoCrypt - Enkripsi')
        self.window.geometry('700x700')
        
        self.img_path = None
        self.original_format = None
        self.photo = None
        self.image_array = None
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Header
        header = tk.Label(self.window, text='Proses Enkripsi Gambar', font=('Arial', 14, 'bold'), bg='#6C5CE7', fg='white')
        header.pack(fill='x', pady=10)
        
        # Frame untuk kontrol
        control_frame = tk.Frame(self.window)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(control_frame, text='1. Pilih Gambar', command=self.load_image, width=30, bg='#6C5CE7', fg='white').pack(side='left', padx=5)
        
        # Canvas untuk preview
        self.canvas = tk.Canvas(self.window, width=512, height=512, bg='gray')
        self.canvas.pack(pady=10)
        
        # Frame untuk password dan tombol
        action_frame = tk.Frame(self.window)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(action_frame, text='Password:', font=('Arial', 10)).pack(side='left', padx=5)
        self.pass_entry = tk.Entry(action_frame, show='*', width=20)
        self.pass_entry.pack(side='left', padx=5)
        
        tk.Button(action_frame, text='2. Enkripsi & Simpan', command=self.encrypt, bg='#6C5CE7', fg='white', width=20).pack(side='left', padx=5)
        tk.Button(action_frame, text='Kembali', command=self.on_close).pack(side='right', padx=5)
        
        # Status label
        self.status_label = tk.Label(self.window, text='Siap untuk memilih gambar...', font=('Arial', 9))
        self.status_label.pack(pady=5)
    
    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff')])
        if not p:
            return
        
        self.img_path = p
        self.original_format = os.path.splitext(p)[1].lower()
        arr, ch, size = load_image(p)
        self.image_array = arr
        
        # Deteksi mode
        if self.image_array.ndim == 2:
            mode = 'Grayscale'
        else:
            mode = 'RGB'
        
        img = Image.fromarray(arr)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.status_label.config(text=f'Gambar: {os.path.basename(p)} | Mode: {mode} | Format: {self.original_format}')
    
    def encrypt(self):
        if self.img_path is None:
            messagebox.showwarning('Peringatan', 'Pilih gambar terlebih dahulu!')
            return
        
        pwd = self.pass_entry.get()
        if not pwd:
            messagebox.showwarning('Peringatan', 'Masukkan password!')
            return
        
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='terenkripsi.png',
                                           filetypes=[('PNG files', '*.png'), ('All files', '*.*')])
        if not out:
            return
        
        try:
            self.status_label.config(text='Proses: Loading gambar...')
            self.window.update()
            
            # Load gambar asli
            from PIL import Image as PILImage
            pil_img = PILImage.open(self.img_path)
            
            # Deteksi mode asli
            original_mode = pil_img.mode
            if original_mode not in ('RGB', 'L'):
                pil_img = pil_img.convert('RGB')
                detected_mode = 'RGB'
            else:
                detected_mode = original_mode
            
            self.status_label.config(text='Proses: Resize ke 512x512...')
            self.window.update()
            
            # Resize ke 512x512
            pil_img = pil_img.resize((512, 512), PILImage.LANCZOS)
            
            # Convert ke numpy array
            image_array = np.array(pil_img, dtype=np.uint8)
            
            self.status_label.config(text='Proses: Enkripsi...')
            self.window.update()
            
            # Enkripsi
            encryp.encrypt_image(image_array, self.original_format, out, pwd)
            messagebox.showinfo('Berhasil', f'Gambar berhasil dienkripsi!\nMode: {detected_mode} | Ukuran: 512x512\nTersimpan: {out}')
            self.status_label.config(text='✓ Enkripsi berhasil!')
        except Exception as e:
            messagebox.showerror('Error', f'Gagal enkripsi: {str(e)}')
            self.status_label.config(text='✗ Enkripsi gagal!')
    
    def on_close(self):
        self.window.destroy()
        self.parent.deiconify()



class DecryptWindow:
    """Window untuk proses dekripsi"""
    def __init__(self, window, parent):
        self.window = window
        self.parent = parent
        self.window.title('StegoCrypt - Dekripsi')
        self.window.geometry('700x700')
        
        self.img_path = None
        self.photo = None
        self.image_array = None
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Header
        header = tk.Label(self.window, text='Proses Dekripsi Gambar', font=('Arial', 14, 'bold'), bg='#00B894', fg='white')
        header.pack(fill='x', pady=10)
        
        # Frame untuk kontrol
        control_frame = tk.Frame(self.window)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(control_frame, text='1. Pilih Gambar Terenkripsi', command=self.load_image, width=30, bg='#00B894', fg='white').pack(side='left', padx=5)
        
        # Canvas untuk preview
        self.canvas = tk.Canvas(self.window, width=512, height=512, bg='gray')
        self.canvas.pack(pady=10)
        
        # Frame untuk password dan tombol
        action_frame = tk.Frame(self.window)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(action_frame, text='Password:', font=('Arial', 10)).pack(side='left', padx=5)
        self.pass_entry = tk.Entry(action_frame, show='*', width=20)
        self.pass_entry.pack(side='left', padx=5)
        
        tk.Button(action_frame, text='2. Dekripsi & Simpan', command=self.decrypt, bg='#00B894', fg='white', width=20).pack(side='left', padx=5)
        tk.Button(action_frame, text='Kembali', command=self.on_close).pack(side='right', padx=5)
        
        # Status label
        self.status_label = tk.Label(self.window, text='Siap untuk memilih gambar terenkripsi...', font=('Arial', 9))
        self.status_label.pack(pady=5)
    
    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg')])
        if not p:
            return
        
        self.img_path = p
        arr, ch, size = load_image(p)
        self.image_array = arr
        
        img = Image.fromarray(arr)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.status_label.config(text=f'Gambar dimuat: {os.path.basename(p)}')
    
    def decrypt(self):
        if not self.img_path:
            messagebox.showwarning('Peringatan', 'Pilih gambar terenkripsi terlebih dahulu!')
            return
        
        pwd = self.pass_entry.get()
        if not pwd:
            messagebox.showwarning('Peringatan', 'Masukkan password!')
            return
        
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='dekripsi.png',
                                           filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp'), ('All files', '*.*')])
        if not out:
            return
        
        try:
            self.status_label.config(text='Proses dekripsi...')
            self.window.update()
            
            result = decryp.decrypt_image(self.img_path, out, pwd)
            if result['success']:
                messagebox.showinfo('Berhasil', f'Gambar berhasil didekripsi!\nFormat asli: {result["format"]}\nTersimpan: {out}')
                self.status_label.config(text='Dekripsi berhasil!')
            else:
                messagebox.showerror('Gagal', f'Dekripsi gagal: {result["error"]}')
                self.status_label.config(text='Dekripsi gagal - password mungkin salah')
        except Exception as e:
            messagebox.showerror('Error', f'Terjadi kesalahan: {str(e)}')
    
    def on_close(self):
        self.window.destroy()
        self.parent.deiconify()



if __name__ == '__main__':
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()
