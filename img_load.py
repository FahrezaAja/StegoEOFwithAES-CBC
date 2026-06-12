
from PIL import Image  # Library Pillow untuk pemrosesan gambar
import numpy as np     # NumPy untuk operasi array piksel


# ─── Konstanta ────────────────────────────────────────────────────────────────

TARGET_SIZE = (512, 512)  # Ukuran target resize gambar

# Peta format extension → nama format PIL
FORMAT_MAP = {
    '.png':  'PNG',
    '.jpg':  'JPEG',
    '.jpeg': 'JPEG',
    '.bmp':  'BMP',
    '.tif':  'TIFF',
    '.tiff': 'TIFF',
}


# ─── Fungsi Utama ──────────────────────────────────────────────────────────────

def load_and_prepare(path: str):
    img = Image.open(path)  # Buka file gambar dari disk

    original_mode = img.mode  # Simpan mode asli sebelum konversi

    # ── Bersihkan mode gambar ──────────────────────────────────────────────────
    if original_mode == 'RGBA':
        # RGBA (ada alpha transparan) → buang channel alpha, jadikan RGB
        img = img.convert('RGB')
        mode = 'RGB'
    elif original_mode == 'LA':
        # LA (grayscale + alpha) → buang channel alpha, jadikan L (grayscale murni)
        img = img.convert('L')
        mode = 'L'
    elif original_mode == 'RGB':
        # Sudah RGB, tidak perlu konversi
        mode = 'RGB'
    elif original_mode == 'L':
        # Sudah grayscale murni, tidak perlu konversi
        mode = 'L'
    else:
        # Mode lain (P, CMYK, YCbCr, dll.) → paksa ke RGB sebagai fallback aman
        img = img.convert('RGB')
        mode = 'RGB'

    # ── Resize ke 512x512 ─────────────────────────────────────────────────────
    img = img.resize(TARGET_SIZE, Image.LANCZOS)  # Resize dengan algoritma LANCZOS (kualitas terbaik)

    # ── Konversi ke NumPy array ────────────────────────────────────────────────
    arr = np.array(img, dtype=np.uint8)  # Buat array piksel dengan tipe data uint8 (0-255)

    # Hitung jumlah channel berdasarkan dimensi array
    channels = 1 if arr.ndim == 2 else arr.shape[2]  # 2D = grayscale (1 ch), 3D = RGB (3 ch)

    return img, arr, mode, channels  # Kembalikan semua hasil


def save_image(pil_img_or_arr, out_path: str, mode: str = 'RGB'):
    import os  # Import os untuk mengambil extension file

    # Konversi input ke PIL Image jika berupa numpy array
    if isinstance(pil_img_or_arr, np.ndarray):
        img = Image.fromarray(pil_img_or_arr)  # Buat PIL Image dari array
    else:
        img = pil_img_or_arr  # Sudah berupa PIL Image

    # Ambil extension dari path output
    ext = os.path.splitext(out_path)[1].lower()  # Contoh: '.png', '.jpg'

    # Tentukan format PIL dari extension
    pil_format = FORMAT_MAP.get(ext, 'PNG')  # Default ke PNG jika extension tidak dikenal

    # Pastikan mode gambar sesuai sebelum menyimpan
    if pil_format == 'JPEG':
        # JPEG tidak mendukung mode L dengan benar di semua versi, tapi PIL biasanya OK
        # JPEG juga tidak mendukung RGBA — pastikan sudah bersih
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')  # Paksa ke RGB jika mode tidak kompatibel dengan JPEG

    img.save(out_path, format=pil_format)  # Simpan gambar ke disk

    return out_path  # Kembalikan path output


def array_to_bytes(arr: np.ndarray) -> bytes:
    return arr.tobytes()  # Flatten array menjadi bytes (urutan C/row-major)


def bytes_to_array(raw: bytes, channels: int, size: tuple) -> np.ndarray:
    w, h = size  # Pisahkan width dan height dari tuple

    if channels == 3:
        # RGB: bentuk array 3D (tinggi, lebar, 3 channel)
        return np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))
    else:
        # Grayscale: bentuk array 2D (tinggi, lebar)
        return np.frombuffer(raw, dtype=np.uint8).reshape((h, w))
