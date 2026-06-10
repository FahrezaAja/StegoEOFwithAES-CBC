from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, HMAC
from image_load import load_image, bytes_to_array, array_to_bytes, save_array_as_image
import json
import os


def derive_key(password: str, salt: bytes, dklen=32, iterations=200000):
    return PBKDF2(password.encode('utf-8'), salt, dkLen=dklen, count=iterations, hmac_hash_module=SHA256)


def decrypt_image(input_path, output_path, password):
    """
    Dekripsi gambar
    Args:
        input_path: path gambar terenkripsi
        output_path: path untuk menyimpan gambar yang didekripsi
        password: password untuk dekripsi
    
    Returns:
        dict: {'success': bool, 'format': str, 'error': str (jika ada)}
    """
    try:
        arr, channels, size = load_image(input_path)
        flat = array_to_bytes(arr)
        total = len(flat)
        if total < 64:
            return {'success': False, 'error': 'Gambar terlalu kecil'}
        
        flat_arr = bytearray(flat)
        
        # Ekstrak salt, iv, dan metadata dari 32 byte terakhir
        iv = bytes(flat_arr[-16:])
        salt = bytes(flat_arr[-32:-16])
        metadata_bytes = bytes(flat_arr[-32:])
        
        # Derive key dari password dan salt
        key = derive_key(password, salt)
        
        # Dekripsi ciphertext
        ciphertext = bytes(flat_arr[: total - 32])
        
        if len(ciphertext) % 16 != 0:
            return {'success': False, 'error': 'Panjang ciphertext tidak valid; gambar rusak atau parameter salah'}
        
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = cipher.decrypt(ciphertext)
        except Exception as e:
            return {'success': False, 'error': f'Dekripsi gagal - password mungkin salah'}
        
        # Baca metadata dari byte terakhir
        try:
            # Cari null terminator
            metadata_str = metadata_bytes.rstrip(b'\0').decode('utf-8')
            metadata = json.loads(metadata_str)
            original_format = metadata.get('format', '.png')
        except:
            original_format = '.png'
        
        # Rekonstruksi array dengan plaintext + metadata
        reconstructed = plaintext + metadata_bytes
        
        out_arr = bytes_to_array(reconstructed, channels, size)
        
        # Simpan dengan format asli jika tersedia
        if not output_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            output_path = output_path + original_format
        else:
            # Jika sudah ada extension, ganti dengan yang sesuai metadata
            base_name = os.path.splitext(output_path)[0]
            output_path = base_name + original_format
        
        save_array_as_image(out_arr, output_path, original_format)
        
        return {
            'success': True,
            'format': original_format,
            'output': output_path
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error dekripsi: {str(e)}'}
