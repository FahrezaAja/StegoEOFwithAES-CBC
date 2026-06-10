from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from image_load import load_image, bytes_to_array, array_to_bytes, save_array_as_image
import numpy as np
import json


def derive_key(password: str, salt: bytes, dklen=32, iterations=200000):
    return PBKDF2(password.encode('utf-8'), salt, dkLen=dklen, count=iterations, hmac_hash_module=SHA256)


def encrypt_image(image_array, original_format, output_path, password):
    """
    Enkripsi gambar
    Args:
        image_array: numpy array dari gambar
        original_format: format asli gambar (contoh: '.png', '.jpg')
        output_path: path untuk menyimpan gambar terenkripsi
        password: password untuk enkripsi
    """
    # Konversi array ke bytes
    flat = array_to_bytes(image_array)
    channels = 1 if image_array.ndim == 2 else image_array.shape[2]
    size = (image_array.shape[1], image_array.shape[0])
    
    total = len(flat)
    if total < 64:
        raise ValueError('Gambar terlalu kecil')
    
    # Metadata format gambar (disimpan di 32 byte terakhir)
    metadata = {'format': original_format, 'channels': channels}
    metadata_str = json.dumps(metadata)
    metadata_bytes = metadata_str.encode('utf-8')[:32].ljust(32, b'\0')
    
    flat_arr = bytearray(flat)
    # Simpan metadata di akhir
    for i in range(total - 32, total):
        flat_arr[i] = metadata_bytes[i - (total - 32)]
    
    salt = get_random_bytes(16)
    iv = get_random_bytes(16)
    key = derive_key(password, salt)
    
    data_to_encrypt = bytes(flat_arr[: total - 32])
    
    if len(data_to_encrypt) % 16 != 0:
        raise ValueError('Panjang plaintext harus kelipatan 16. Untuk RGB 512x512 pastikan reserved bytes diatur.')
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(data_to_encrypt)
    
    combined = ciphertext + salt + iv
    
    if len(combined) != total:
        raise ValueError(f'Ukuran gabungan tidak sesuai: {len(combined)} != {total}')
    
    out_arr = bytes_to_array(combined, channels, size)
    save_array_as_image(out_arr, output_path if output_path.lower().endswith('.png') else output_path + '.png')
    return output_path
