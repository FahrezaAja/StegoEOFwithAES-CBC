import struct  # Untuk packing/unpacking data biner (header numerik)


# ─── Konstanta ────────────────────────────────────────────────────────────────

EOF_MAGIC = b'STGEOF00'  # Tanda pengenal / magic bytes untuk header EOF (8 byte)
HEADER_SIZE = 16          # Ukuran header tetap dalam byte


# ─── Fungsi Embed ──────────────────────────────────────────────────────────────

def embed(host_path: str, payload: bytes, original_format: str, mode: str, output_path: str):
    if not payload:
        raise ValueError('Payload tidak boleh kosong.')  # Validasi payload tidak kosong

    # ── Baca byte asli gambar host ─────────────────────────────────────────────
    with open(host_path, 'rb') as f:
        host_bytes = f.read()  # Baca semua byte file gambar host sebagai binary

    # ── Encode string ke bytes ─────────────────────────────────────────────────
    fmt_bytes  = original_format.encode('utf-8')  # Encode format string ke bytes, misal b'.png'
    mode_bytes = mode.encode('utf-8')              # Encode mode string ke bytes, misal b'RGB'

    # ── Buat header 16 byte ────────────────────────────────────────────────────
    # Format struct: '8s' = 8 byte string, 'I' = uint32, 'H' = uint16, 'H' = uint16
    header = struct.pack(
        '>8sIHH',          # Big-endian: magic(8) + payload_len(4) + fmt_len(2) + mode_len(2) = 16 byte
        EOF_MAGIC,         # Magic signature 8 byte
        len(payload),      # Panjang payload terenkripsi (uint32)
        len(fmt_bytes),    # Panjang string format (uint16)
        len(mode_bytes),   # Panjang string mode (uint16)
    )

    # ── Tulis file output ──────────────────────────────────────────────────────
    with open(output_path, 'wb') as f:
        f.write(host_bytes)  # Tulis byte gambar host (tetap valid sebagai gambar)
        f.write(header)      # Tulis header EOF (16 byte)
        f.write(fmt_bytes)   # Tulis string format asli
        f.write(mode_bytes)  # Tulis string mode gambar
        f.write(payload)     # Tulis payload terenkripsi

    return output_path  # Kembalikan path file yang berhasil ditulis


# ─── Fungsi Extract ────────────────────────────────────────────────────────────

def extract(stego_path: str):
    # ── Baca seluruh byte file ─────────────────────────────────────────────────
    with open(stego_path, 'rb') as f:
        data = f.read()  # Baca semua byte file stego sebagai binary

    # ── Cari posisi magic signature ────────────────────────────────────────────
    # Cari dari akhir file ke depan (rfind = reverse find) untuk efisiensi
    magic_pos = data.rfind(EOF_MAGIC)  # Temukan posisi terakhir kemunculan magic bytes

    if magic_pos == -1:
        # Magic tidak ditemukan → gambar ini bukan hasil enkripsi aplikasi ini
        raise ValueError(
            'Tidak ditemukan data tersembunyi (magic signature tidak ada).\n'
            'Pastikan gambar ini adalah hasil enkripsi dari aplikasi StegoCrypt.'
        )

    # ── Parse header 16 byte ──────────────────────────────────────────────────
    header_bytes = data[magic_pos: magic_pos + HEADER_SIZE]  # Ambil tepat 16 byte header

    if len(header_bytes) < HEADER_SIZE:
        raise ValueError('Header EOF tidak lengkap — file mungkin rusak.')  # Validasi panjang header

    # Unpack header sesuai format struct yang digunakan saat embed
    magic_read, payload_len, fmt_len, mode_len = struct.unpack('>8sIHH', header_bytes)

    # Verifikasi ulang magic signature yang dibaca dari header
    if magic_read != EOF_MAGIC:
        raise ValueError('Magic signature tidak valid — file mungkin rusak.')

    # ── Hitung posisi data setelah header ─────────────────────────────────────
    after_header = magic_pos + HEADER_SIZE  # Posisi byte pertama setelah header

    # Ekstrak string format asli
    fmt_bytes  = data[after_header: after_header + fmt_len]  # Ambil bytes format
    after_fmt  = after_header + fmt_len                       # Posisi setelah format

    # Ekstrak string mode gambar
    mode_bytes = data[after_fmt: after_fmt + mode_len]        # Ambil bytes mode
    after_mode = after_fmt + mode_len                         # Posisi setelah mode

    # Ekstrak payload terenkripsi
    payload = data[after_mode: after_mode + payload_len]      # Ambil payload sesuai panjang

    # Validasi panjang payload yang diekstrak
    if len(payload) != payload_len:
        raise ValueError(
            f'Panjang payload tidak sesuai: diharapkan {payload_len}, didapat {len(payload)}. '
            'File mungkin rusak atau tidak lengkap.'
        )

    # Decode string format dan mode dari bytes
    original_format = fmt_bytes.decode('utf-8')   # Contoh: '.png'
    mode            = mode_bytes.decode('utf-8')  # Contoh: 'RGB'

    return payload, original_format, mode  # Kembalikan tuple hasil ekstraksi


# ─── Fungsi Utilitas ──────────────────────────────────────────────────────────

def has_eof_data(file_path: str) -> bool:
    try:
        with open(file_path, 'rb') as f:
            data = f.read()              # Baca semua byte file
        return data.rfind(EOF_MAGIC) != -1  # Cek apakah magic signature ada
    except Exception:
        return False  # Jika ada error (misal file tidak ada), kembalikan False


def peek_format(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        magic_pos = data.rfind(EOF_MAGIC)
        if magic_pos == -1:
            return '.png'  # Fallback jika tidak ditemukan

        header_bytes = data[magic_pos: magic_pos + HEADER_SIZE]
        if len(header_bytes) < HEADER_SIZE:
            return '.png'

        _, _, fmt_len, _ = struct.unpack('>8sIHH', header_bytes)

        after_header = magic_pos + HEADER_SIZE
        fmt_bytes = data[after_header: after_header + fmt_len]

        return fmt_bytes.decode('utf-8')  # Contoh: '.png', '.tiff', '.jpg'
    except Exception:
        return '.png'  # Fallback default
