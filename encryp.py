from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from image_load import load_image, bytes_to_array, array_to_bytes, save_array_as_image
import numpy as np


def derive_key(password: str, salt: bytes, dklen=32, iterations=200000):
    return PBKDF2(password.encode('utf-8'), salt, dkLen=dklen, count=iterations, hmac_hash_module=SHA256)


def encrypt_image(input_path, output_path, password):
    arr, channels, size = load_image(input_path)
    flat = array_to_bytes(arr)
    total = len(flat)
    if total < 32:
        raise ValueError('Image too small')

    flat_arr = bytearray(flat)
    for i in range(total - 32, total):
        flat_arr[i] = 0

    salt = get_random_bytes(16)
    iv = get_random_bytes(16)
    key = derive_key(password, salt)

    data_to_encrypt = bytes(flat_arr[: total - 32])

    if len(data_to_encrypt) % 16 != 0:
        raise ValueError('Plaintext length must be multiple of 16. For 512x512 RGB channel ensure reserved bytes set.')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(data_to_encrypt)

    combined = ciphertext + salt + iv

    if len(combined) != total:
        raise ValueError(f'Combined size mismatch: {len(combined)} != {total}')

    out_arr = bytes_to_array(combined, channels, size)
    save_array_as_image(out_arr, output_path if output_path.lower().endswith('.png') else output_path + '.png')
    return output_path
