import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import numpy as np
from image_load import load_image, save_array_as_image
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
        self.password = None
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Header
        header = tk.Label(self.window, text='Enkripsi Gambar', font=('Arial', 14, 'bold'), bg='#6C5CE7', fg='white')
        header.pack(fill='x', pady=3)
        
        # Tombol utama
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text='Masukkan Gambar', command=self.load_image, width=26, height=2,
                  bg='#6C5CE7', fg='white', font=('Arial', 11, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(side='left', padx=12)
        tk.Button(button_frame, text='Masukkan Password', command=self.ask_password, width=26, height=2,
                  bg='#5D6AE9', fg='white', font=('Arial', 11, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(side='left', padx=12)
        
        # Preview image
        self.canvas = tk.Canvas(self.window, width=512, height=512, bg='gray')
        self.canvas.pack(pady=5)
        
        # Password display
        self.pass_label = tk.Label(self.window, text='Password: belum dimasukkan', font=('Arial', 9))
        self.pass_label.pack(pady=2)
        
        # Simpan
        tk.Button(self.window, text='Simpan & Enkripsi', command=self.encrypt, bg='#6C5CE7', fg='white', width=24, height=1,
                  font=('Arial', 10, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(pady=3)
        
        # Kembali button frame
        button_back_frame = tk.Frame(self.window)
        button_back_frame.pack(pady=3)
        tk.Button(button_back_frame, text='Kembali', command=self.on_close, width=12, height=1,
                  bd=2, relief='groove', highlightthickness=0).pack()
        
        self.status_label = tk.Label(self.window, text='Silakan masukkan gambar dan password.', font=('Arial', 8))
        self.status_label.pack(pady=2)
    
    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff')])
        if not p:
            return
        
        self.img_path = p
        self.original_format = os.path.splitext(p)[1].lower()
        arr, ch, size = load_image(p)
        self.image_array = arr
        self.preview_image()
        self.status_label.config(text=f'Gambar dipilih: {os.path.basename(p)}')
    
    def ask_password(self):
        pwd = simpledialog.askstring('Masukkan Password', 'Masukkan password untuk enkripsi:', show='*', parent=self.window)
        if pwd is None:
            return
        self.password = pwd
        self.pass_label.config(text='Password: dimasukkan')
        self.status_label.config(text='Password sudah diatur.')
    
    def preview_image(self):
        if self.image_array is None:
            messagebox.showwarning('Peringatan', 'Tidak ada gambar untuk ditampilkan.')
            return
        img = Image.fromarray(self.image_array)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.status_label.config(text='Preview gambar ditampilkan.')
    
    def encrypt(self):
        if self.img_path is None:
            messagebox.showwarning('Peringatan', 'Pilih gambar terlebih dahulu!')
            return
        if not self.password:
            messagebox.showwarning('Peringatan', 'Masukkan password terlebih dahulu!')
            return
        
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='terenkripsi.png',
                                           filetypes=[('PNG files', '*.png'), ('All files', '*.*')])
        if not out:
            return
        
        try:
            self.status_label.config(text='Memproses enkripsi...')
            self.window.update()
            
            from PIL import Image as PILImage
            pil_img = PILImage.open(self.img_path)
            original_mode = pil_img.mode
            if original_mode not in ('RGB', 'L'):
                pil_img = pil_img.convert('RGB')
                detected_mode = 'RGB'
            else:
                detected_mode = original_mode
            
            pil_img = pil_img.resize((512, 512), PILImage.LANCZOS)
            image_array = np.array(pil_img, dtype=np.uint8)
            encryp.encrypt_image(image_array, self.original_format, out, self.password)
            messagebox.showinfo('Berhasil', f'Gambar berhasil dienkripsi!\nMode: {detected_mode} | Ukuran: 512x512\nTersimpan: {out}')
            self.status_label.config(text='Enkripsi selesai.')
        except Exception as e:
            messagebox.showerror('Error', f'Gagal enkripsi: {str(e)}')
            self.status_label.config(text='Enkripsi gagal.')
    
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
        self.password = None
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Header
        header = tk.Label(self.window, text='Dekripsi Gambar', font=('Arial', 14, 'bold'), bg='#00B894', fg='white')
        header.pack(fill='x', pady=3)
        
        # Tombol utama
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text='Masukkan Gambar', command=self.load_image, width=26, height=2,
                  bg='#00B894', fg='white', font=('Arial', 11, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(side='left', padx=12)
        tk.Button(button_frame, text='Masukkan Password', command=self.ask_password, width=26, height=2,
                  bg='#3BAF7D', fg='white', font=('Arial', 11, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(side='left', padx=12)
        
        # Preview image
        self.canvas = tk.Canvas(self.window, width=512, height=512, bg='white')
        self.canvas.pack(pady=5)
        
        # Password display
        self.pass_label = tk.Label(self.window, text='Password: belum dimasukkan', font=('Arial', 9))
        self.pass_label.pack(pady=2)
        
        # Simpan
        tk.Button(self.window, text='Simpan & Dekripsi', command=self.decrypt, bg='#00B894', fg='white', width=24, height=1,
                  font=('Arial', 10, 'bold'), bd=2, relief='groove', highlightthickness=0).pack(pady=3)
        
        # Kembali button frame
        button_back_frame = tk.Frame(self.window)
        button_back_frame.pack(pady=3)
        tk.Button(button_back_frame, text='Kembali', command=self.on_close, width=12, height=1,
                  bd=2, relief='groove', highlightthickness=0).pack()
        
        self.status_label = tk.Label(self.window, text='Silakan masukkan gambar terenkripsi dan password.', font=('Arial', 8))
        self.status_label.pack(pady=2)
    
    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp')])
        if not p:
            return
        
        self.img_path = p
        arr, ch, size = load_image(p)
        self.image_array = arr
        self.preview_image()
        self.status_label.config(text=f'Gambar dienkripsi dipilih: {os.path.basename(p)}')
    
    def ask_password(self):
        pwd = simpledialog.askstring('Masukkan Password', 'Masukkan password untuk dekripsi:', show='*', parent=self.window)
        if pwd is None:
            return
        self.password = pwd
        self.pass_label.config(text='Password: dimasukkan')
        self.status_label.config(text='Password sudah diatur.')
    
    def preview_image(self):
        if self.image_array is None:
            messagebox.showwarning('Peringatan', 'Tidak ada gambar untuk ditampilkan.')
            return
        img = Image.fromarray(self.image_array)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.status_label.config(text='Preview gambar ditampilkan.')
    
    def decrypt(self):
        if self.img_path is None:
            messagebox.showwarning('Peringatan', 'Pilih gambar terenkripsi terlebih dahulu!')
            return
        if not self.password:
            messagebox.showwarning('Peringatan', 'Masukkan password terlebih dahulu!')
            return
        
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='dekripsi.png',
                                           filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp'), ('All files', '*.*')])
        if not out:
            return
        
        try:
            self.status_label.config(text='Memproses dekripsi...')
            self.window.update()
            
            result = decryp.decrypt_image(self.img_path, out, self.password)
            if result['success']:
                messagebox.showinfo('Berhasil', f'Gambar berhasil didekripsi!\nFormat asli: {result["format"]}\nTersimpan: {out}')
                self.status_label.config(text='Dekripsi selesai.')
            else:
                messagebox.showerror('Gagal', f'Dekripsi gagal: {result["error"]}')
                self.status_label.config(text='Dekripsi gagal.')
        except Exception as e:
            messagebox.showerror('Error', f'Terjadi kesalahan: {str(e)}')
            self.status_label.config(text='Dekripsi gagal.')
    
    def on_close(self):
        self.window.destroy()
        self.parent.deiconify()



if __name__ == '__main__':
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()
