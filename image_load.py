from PIL import Image
import numpy as np


def load_image(path, size=(512, 512)):
    img = Image.open(path)
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    arr = np.array(img, dtype=np.uint8)
    channels = 1 if arr.ndim == 2 else arr.shape[2]
    return arr, channels, size


def apply_image_processing(arr, mode='RGB', size=(512, 512)):
    """Terapkan pengolahan citra: konversi mode dan resize"""
    img = Image.fromarray(arr)
    
    # Resize ke 512x512
    img = img.resize(size, Image.LANCZOS)
    
    # Konversi mode
    if mode == 'RGB':
        if img.mode != 'RGB':
            img = img.convert('RGB')
    elif mode == 'Grayscale':
        img = img.convert('L')
    
    arr = np.array(img, dtype=np.uint8)
    return arr


def save_array_as_image(arr, out_path, format_type=None):
    """Simpan array sebagai gambar dengan format tertentu"""
    img = Image.fromarray(arr)
    if format_type:
        # Gunakan format yang ditentukan
        format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.bmp': 'BMP', '.tif': 'TIFF', '.tiff': 'TIFF'}
        pil_format = format_map.get(format_type.lower(), 'PNG')
        img.save(out_path, format=pil_format)
    else:
        # Deteksi dari extension
        img.save(out_path)
    return out_path


def bytes_to_array(bytes_buf, channels, size):
    if channels == 3:
        arr = np.frombuffer(bytes_buf, dtype=np.uint8).reshape((size[1], size[0], 3))
    else:
        arr = np.frombuffer(bytes_buf, dtype=np.uint8).reshape((size[1], size[0]))
    return arr


def array_to_bytes(arr):
    return arr.tobytes()
