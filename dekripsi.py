import os                                  # Untuk operasi path file
from Crypto.Cipher import AES              # AES cipher dari pycryptodome
from Crypto.Protocol.KDF import PBKDF2    # Fungsi Key Derivation PBKDF2
from Crypto.Hash import SHA256             # Hash SHA256 untuk PBKDF2

import img_load  # Modul integritas data gambar
import eof       # Modul steganografi EOF


# ─── Konstanta ────────────────────────────────────────────────────────────────

SALT_SIZE   = 16        # Ukuran salt dalam byte (harus sama dengan enkripsi.py)
IV_SIZE     = 16        # Ukuran IV AES-CBC dalam byte (harus sama dengan enkripsi.py)
KEY_SIZE    = 32        # Ukuran kunci AES-256 dalam byte
PBKDF2_ITER = 200_000   # Jumlah iterasi PBKDF2 (harus sama persis dengan saat enkripsi)
TARGET_SIZE = (512, 512)  # Ukuran gambar yang diharapkan setelah dekripsi


# ─── Fungsi Bantu ──────────────────────────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(
        password.encode('utf-8'),  # Encode password ke bytes UTF-8
        salt,                      # Salt yang sama seperti saat enkripsi
        dkLen=KEY_SIZE,            # Panjang kunci = 32 byte
        count=PBKDF2_ITER,         # Iterasi yang sama dengan enkripsi
        hmac_hash_module=SHA256,   # Hash SHA256 yang sama
    )


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError('Data hasil dekripsi kosong.')  # Validasi data tidak kosong

    pad_len = data[-1]  # Byte terakhir = nilai padding

    # Validasi rentang nilai padding (1-16 untuk blok AES 16 byte)
    if pad_len < 1 or pad_len > 16:
        raise ValueError(
            f'Padding tidak valid (nilai: {pad_len}). '
            'Password mungkin salah atau data rusak.'
        )

    # Validasi semua byte padding bernilai pad_len
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError(
            'Padding tidak konsisten. '
            'Password kemungkinan salah atau data telah rusak.'
        )

    return data[:-pad_len]  # Kembalikan data tanpa byte padding


# ─── Fungsi Utama ──────────────────────────────────────────────────────────────

def decrypt_image(stego_path: str, output_path: str, password: str) -> dict:
    try:
        # ── LANGKAH 1: Deteksi apakah file memiliki data EOF ───────────────────
        if not eof.has_eof_data(stego_path):
            # Gambar tidak memiliki magic signature → bukan hasil enkripsi aplikasi ini
            return {
                'success': False,
                'error'  : (
                    'Gambar ini BUKAN hasil enkripsi dari aplikasi StegoCrypt.\n'
                    'Tidak ditemukan data tersembunyi dalam file ini.\n'
                    'Pastikan Anda memilih gambar yang sudah dienkripsi terlebih dahulu.'
                ),
            }

        # ── LANGKAH 2: Ekstrak payload dari EOF ────────────────────────────────
        try:
            payload, original_format, mode = eof.extract(stego_path)  # Ekstrak data EOF
        except ValueError as e:
            # Error ekstraksi → data rusak atau bukan file valid
            return {'success': False, 'error': str(e)}

        # ── LANGKAH 3: Pisahkan salt, iv, dan ciphertext dari payload ──────────
        if len(payload) < SALT_SIZE + IV_SIZE:
            # Payload terlalu pendek untuk mengandung salt + iv + ciphertext
            return {
                'success': False,
                'error'  : 'Payload terlalu pendek — data mungkin rusak atau tidak valid.',
            }

        salt       = payload[:SALT_SIZE]                      # 16 byte pertama = salt
        iv         = payload[SALT_SIZE: SALT_SIZE + IV_SIZE]  # 16 byte berikutnya = IV
        ciphertext = payload[SALT_SIZE + IV_SIZE:]            # Sisa = ciphertext

        # Validasi panjang ciphertext harus kelipatan 16 (ukuran blok AES)
        if len(ciphertext) % 16 != 0:
            return {
                'success': False,
                'error'  : 'Panjang ciphertext tidak valid (bukan kelipatan 16). Data mungkin rusak.',
            }

        # ── LANGKAH 4: Derivasi kunci dari password + salt ─────────────────────
        key = _derive_key(password, salt)  # Hasilkan kunci 32 byte

        # ── LANGKAH 5: Dekripsi dengan AES-CBC ─────────────────────────────────
        try:
            cipher    = AES.new(key, AES.MODE_CBC, iv)  # Buat objek cipher AES-CBC dengan key & iv
            decrypted = cipher.decrypt(ciphertext)       # Dekripsi ciphertext
        except Exception as e:
            # Error pada cipher → kemungkinan IV atau key rusak
            return {
                'success': False,
                'error'  : f'Dekripsi AES gagal: {str(e)}. Password mungkin salah.',
            }

        # ── LANGKAH 6: Validasi dan hapus PKCS#7 padding ───────────────────────
        try:
            raw_bytes = _pkcs7_unpad(decrypted)  # Hapus padding dan validasi
        except ValueError as e:
            # Padding tidak valid → PASSWORD SALAH (paling umum)
            return {
                'success': False,
                'error'  : (
                    f'PASSWORD SALAH atau data rusak.\n'
                    f'Detail teknis: {str(e)}'
                ),
            }

        # ── LANGKAH 7: Rekonstruksi & Simpan hasil dekripsi ────────────────────
        base_out    = os.path.splitext(output_path)[0]    # Nama file tanpa extension
        output_path = base_out + original_format           # Tambah extension asli

        if mode == 'RAW':
            # File mentah (bit-for-bit perfect) langsung ditulis
            with open(output_path, 'wb') as f:
                f.write(raw_bytes)
        else:
            # Mode lama (RGB/L), rekonstruksi piksel lalu simpan via img_load
            channels = 3 if mode == 'RGB' else 1  # Tentukan jumlah channel dari mode
            w, h     = TARGET_SIZE                 # Width dan height gambar

            # Validasi ukuran data sesuai dimensi gambar
            expected_size = w * h * channels  # Jumlah byte yang diharapkan
            if len(raw_bytes) != expected_size:
                return {
                    'success': False,
                    'error'  : (
                        f'Ukuran data piksel tidak sesuai: diharapkan {expected_size} byte, '
                        f'didapat {len(raw_bytes)} byte. '
                        'Password salah atau data rusak.'
                    ),
                }

            # Rekonstruksi array piksel dari bytes mentah
            arr = img_load.bytes_to_array(raw_bytes, channels, TARGET_SIZE)  # Buat array piksel
            img_load.save_image(arr, output_path, mode)  # Simpan array sebagai gambar

        return {
            'success'        : True,
            'output'         : output_path,     # Path file output
            'original_format': original_format, # Format asli gambar
            'mode'           : mode,            # Mode gambar (RGB/L)
        }

    except Exception as e:
        # Tangkap error tak terduga lainnya
        return {
            'success': False,
            'error'  : f'Terjadi kesalahan tak terduga: {str(e)}',
        }
