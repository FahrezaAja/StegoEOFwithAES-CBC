
import os                                  # Untuk operasi path file
import tempfile                            # Untuk membuat file sementara
from Crypto.Cipher import AES              # AES cipher dari pycryptodome
from Crypto.Protocol.KDF import PBKDF2    # Fungsi Key Derivation PBKDF2
from Crypto.Hash import SHA256             # Hash SHA256 untuk PBKDF2
from Crypto.Random import get_random_bytes # Generator byte acak kriptografis

import img_load  # Modul integritas data gambar (load, bersihkan mode, resize, save)
import eof       # Modul steganografi EOF


# ─── Konstanta ────────────────────────────────────────────────────────────────

SALT_SIZE   = 16        # Ukuran salt dalam byte
IV_SIZE     = 16        # Ukuran IV (Initialization Vector) AES-CBC dalam byte
KEY_SIZE    = 32        # Ukuran kunci AES-256 dalam byte (256 bit)
PBKDF2_ITER = 200_000   # Jumlah iterasi PBKDF2 (semakin banyak semakin aman, semakin lambat)


# ─── Fungsi Bantu ──────────────────────────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(
        password.encode('utf-8'),  # Encode password dari string ke bytes UTF-8
        salt,                      # Salt acak untuk mencegah rainbow table attack
        dkLen=KEY_SIZE,            # Panjang kunci yang dihasilkan = 32 byte
        count=PBKDF2_ITER,         # Jumlah iterasi hash
        hmac_hash_module=SHA256,   # Gunakan SHA256 sebagai fungsi hash HMAC
    )


def _pkcs7_pad(data: bytes) -> bytes:
    pad_len = 16 - (len(data) % 16)  # Hitung berapa byte padding yang dibutuhkan
    return data + bytes([pad_len] * pad_len)  # Tambahkan byte padding dengan nilai = pad_len

# ─── Fungsi Utama ──────────────────────────────────────────────────────────────

def encrypt_image(src_path: str, output_path: str, password: str, cover_path: str = None) -> dict:
    tmp_path = None  # Variabel untuk path file sementara

    try:
        # ── LANGKAH 1: Muat & persiapkan gambar SUMBER (yang dienkripsi) ────────
        pil_src, arr, mode, channels = img_load.load_and_prepare(src_path)

        # Ambil extension format asli dari path sumber
        original_format = os.path.splitext(src_path)[1].lower()
        if not original_format:
            original_format = '.png'

        # Pastikan output_path menggunakan extension yang sama dengan format cover
        # (atau sumber jika cover tidak diberikan)
        host_path = cover_path if cover_path else src_path
        cover_ext = os.path.splitext(host_path)[1].lower() or original_format

        base_out    = os.path.splitext(output_path)[0]
        output_path = base_out + cover_ext

        # ── LANGKAH 2: Baca byte MENTAH dari file SUMBER ───────────────────────
        # agar saat didekripsi bit-nya 100% sama persis (bit-for-bit perfect).
        with open(src_path, 'rb') as f:
            raw_bytes = f.read()
        
        mode = 'RAW'  # Tandai bahwa payload adalah raw binary file

        # ── LANGKAH 3: Tambahkan PKCS#7 padding ────────────────────────────────
        padded = _pkcs7_pad(raw_bytes)

        # ── LANGKAH 4: Generate salt & IV acak ─────────────────────────────────
        salt = get_random_bytes(SALT_SIZE)
        iv   = get_random_bytes(IV_SIZE)

        # ── LANGKAH 5: Derivasi kunci AES dari password + salt ─────────────────
        key = _derive_key(password, salt)

        # ── LANGKAH 6: Enkripsi dengan AES-CBC ─────────────────────────────────
        cipher     = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(padded)

        # ── LANGKAH 7: Susun payload ────────────────────────────────────────────
        # Format: [salt (16 byte)] + [iv (16 byte)] + [ciphertext]
        payload = salt + iv + ciphertext

        # ── LANGKAH 8: Muat gambar COVER lalu simpan ke file sementara ──────────
        import shutil
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=cover_ext)
        os.close(tmp_fd)

        if cover_path:
            # Salin cover mentah-mentah agar struktur byte (endian, meta) tidak berubah
            shutil.copy2(cover_path, tmp_path)
        else:
            # Jika tidak ada cover, gunakan gambar asli yang sudah di-resize & dibersihkan
            img_load.save_image(pil_src, tmp_path, mode)

        # ── LANGKAH 9: Sisipkan payload ke gambar cover via EOF ─────────────────
        eof.embed(tmp_path, payload, original_format, mode, output_path)

        return {
            'success': True,
            'output' : output_path,
            'mode'   : mode,
        }

    except Exception as e:
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass

        return {
            'success': False,
            'error'  : str(e),
        }

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
