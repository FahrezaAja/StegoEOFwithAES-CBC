from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from image_load import load_image, bytes_to_array, array_to_bytes, save_array_as_image


def derive_key(password: str, salt: bytes, dklen=32, iterations=200000):
    return PBKDF2(password.encode('utf-8'), salt, dkLen=dklen, count=iterations, hmac_hash_module=SHA256)


def decrypt_image(input_path, output_path, password):
    arr, channels, size = load_image(input_path)
    flat = array_to_bytes(arr)
    total = len(flat)
    if total < 32:
        raise ValueError('Image too small')

    flat_arr = bytearray(flat)
    iv = bytes(flat_arr[-16:])
    salt = bytes(flat_arr[-32:-16])

    key = derive_key(password, salt)

    ciphertext = bytes(flat_arr[: total - 32])

    if len(ciphertext) % 16 != 0:
        raise ValueError('Ciphertext length not multiple of 16; corrupted or wrong parameters.')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext)

    reconstructed = plaintext + bytes([0] * 32)

    out_arr = bytes_to_array(reconstructed, channels, size)
    save_array_as_image(out_arr, output_path if output_path.lower().endswith('.png') else output_path + '.png')
    return output_path
