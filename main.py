import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from image_load import load_image, save_array_as_image, to_grayscale, to_rgb
import encryp, decryp


class App:
    def __init__(self, root):
        self.root = root
        root.title('Image Encryptor')

        self.img_path = None
        self.photo = None

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill='x')

        tk.Button(btn_frame, text='Load Image', command=self.load_image).pack(side='left')
        tk.Button(btn_frame, text='Encrypt', command=self.encrypt).pack(side='left')
        tk.Button(btn_frame, text='Decrypt', command=self.decrypt).pack(side='left')

        self.pass_entry = tk.Entry(btn_frame, show='*')
        self.pass_entry.pack(side='right')
        tk.Label(btn_frame, text='Password:').pack(side='right')

        self.canvas = tk.Canvas(root, width=512, height=512)
        self.canvas.pack()

    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff')])
        if not p:
            return
        self.img_path = p
        arr, ch, size = load_image(p)
        img = Image.fromarray(arr)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

    def encrypt(self):
        if not self.img_path:
            messagebox.showwarning('No image', 'Please load an image first')
            return
        pwd = self.pass_entry.get()
        if not pwd:
            messagebox.showwarning('Password', 'Enter a password')
            return
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='terenkripsi_bawah.png')
        if not out:
            return
        try:
            encryp.encrypt_image(self.img_path, out, pwd)
            messagebox.showinfo('Done', f'Encrypted saved to {out}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def decrypt(self):
        p = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg')])
        if not p:
            return
        pwd = self.pass_entry.get()
        if not pwd:
            messagebox.showwarning('Password', 'Enter a password')
            return
        out = filedialog.asksaveasfilename(defaultextension='.png', initialfile='decrypted.png')
        if not out:
            return
        try:
            decryp.decrypt_image(p, out, pwd)
            messagebox.showinfo('Done', f'Decrypted saved to {out}')
        except Exception as e:
            messagebox.showerror('Error', str(e))


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
