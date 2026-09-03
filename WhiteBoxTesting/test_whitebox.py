
import os
import sys
import tempfile

from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import dekripsi
import eof
import enkripsi


def test_pkcs7_unpad():
    print("=== TEST 1: PKCS#7 UNPAD ===")

    # Data dengan padding valid
    data_valid = b"HELLO" + bytes([11] * 11)

    try:
        hasil = dekripsi._pkcs7_unpad(data_valid)

        if hasil == b"HELLO":
            print("[PASS] Padding valid berhasil dihapus.")
        else:
            print("[FAIL] Hasil unpadding tidak sesuai.")

    except Exception as e:
        print("[FAIL] Terjadi exception:", e)


def test_pkcs7_empty():
    print("\n=== TEST 2: DATA KOSONG ===")

    try:
        dekripsi._pkcs7_unpad(b"")

        print("[FAIL] Data kosong seharusnya menghasilkan error.")

    except ValueError:
        print("[PASS] Data kosong berhasil ditolak.")


def test_pkcs7_invalid_range():
    print("\n=== TEST 3: PADDING DI LUAR RENTANG ===")

    # Nilai padding 0 tidak valid
    data = b"HELLO" + bytes([0])

    try:
        dekripsi._pkcs7_unpad(data)

        print("[FAIL] Padding 0 seharusnya ditolak.")

    except ValueError:
        print("[PASS] Padding dengan nilai 0 berhasil ditolak.")


def test_pkcs7_inconsistent():
    print("\n=== TEST 4: PADDING TIDAK KONSISTEN ===")

    # Padding seharusnya 3 byte bernilai 3,
    # tetapi byte terakhir tidak sesuai.
    data = b"HELLO" + bytes([3, 3, 2])

    try:
        dekripsi._pkcs7_unpad(data)

        print("[FAIL] Padding tidak konsisten seharusnya ditolak.")

    except ValueError:
        print("[PASS] Padding tidak konsisten berhasil ditolak.")


def test_decrypt_without_eof():
    print("\n=== TEST 5: FILE TANPA EOF ===")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        f.write(b"FILE GAMBAR BIASA")
        input_path = f.name

    output_path = input_path + "_output"

    try:
        hasil = dekripsi.decrypt_image(
            input_path,
            output_path,
            "password123"
        )

        if hasil["success"] is False:
            print("[PASS] File tanpa EOF berhasil ditolak.")
            print("       Pesan:", hasil["error"])
        else:
            print("[FAIL] File tanpa EOF seharusnya gagal.")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

        if os.path.exists(output_path):
            os.remove(output_path)


def create_test_image(path):
    """
    Membuat gambar PNG sederhana untuk kebutuhan pengujian.
    File ini valid sehingga dapat diproses oleh img_load.load_and_prepare().
    """

    image = Image.new(
        "RGB",
        (512, 512),
        (120, 180, 220)
    )

    image.save(path, format="PNG")


def test_valid_encrypt_decrypt():
    print("\n=== TEST 6: ENKRIPSI DAN DEKRIPSI VALID ===")

    with tempfile.TemporaryDirectory() as temp:

        source = os.path.join(temp, "source.png")
        encrypted = os.path.join(temp, "encrypted.png")
        decrypted = os.path.join(temp, "decrypted.png")

        password = "password123"

        # Buat gambar PNG valid sebagai data uji
        create_test_image(source)

        # Simpan byte asli untuk perbandingan
        with open(source, "rb") as f:
            original_data = f.read()

        # Enkripsi
        hasil_encrypt = enkripsi.encrypt_image(
            source,
            encrypted,
            password
        )

        if not hasil_encrypt["success"]:
            print("[FAIL] Proses enkripsi gagal.")
            print("       Pesan:", hasil_encrypt["error"])
            return

        print("[PASS] Proses enkripsi berhasil.")

        # Dekripsi menggunakan password yang benar
        hasil_decrypt = dekripsi.decrypt_image(
            hasil_encrypt["output"],
            decrypted,
            password
        )

        if not hasil_decrypt["success"]:
            print("[FAIL] Proses dekripsi gagal.")
            print("       Pesan:", hasil_decrypt["error"])
            return

        print("[PASS] Proses dekripsi berhasil.")

        # Baca hasil dekripsi
        with open(hasil_decrypt["output"], "rb") as f:
            result_data = f.read()

        # Bandingkan byte-per-byte
        if result_data == original_data:
            print("[PASS] Data hasil dekripsi sama persis dengan data asli.")
        else:
            print("[FAIL] Data hasil dekripsi berbeda dengan data asli.")


def test_wrong_password():
    print("\n=== TEST 7: PASSWORD SALAH ===")

    with tempfile.TemporaryDirectory() as temp:

        source = os.path.join(temp, "source.png")
        encrypted = os.path.join(temp, "encrypted.png")
        decrypted = os.path.join(temp, "decrypted.png")

        # Buat gambar PNG valid
        create_test_image(source)

        # Enkripsi dengan password yang benar
        hasil_encrypt = enkripsi.encrypt_image(
            source,
            encrypted,
            "password_benar"
        )

        if not hasil_encrypt["success"]:
            print("[FAIL] Enkripsi gagal.")
            print("       Pesan:", hasil_encrypt["error"])
            return

        print("[PASS] Enkripsi dengan password benar berhasil.")

        # Coba dekripsi menggunakan password yang salah
        hasil_decrypt = dekripsi.decrypt_image(
            hasil_encrypt["output"],
            decrypted,
            "password_salah"
        )

        if hasil_decrypt["success"] is False:
            print("[PASS] Password salah berhasil ditolak.")
            print("       Pesan:", hasil_decrypt["error"])
        else:
            print("[FAIL] Password salah seharusnya ditolak.")


if __name__ == "__main__":

    test_pkcs7_unpad()
    test_pkcs7_empty()
    test_pkcs7_invalid_range()
    test_pkcs7_inconsistent()

    test_decrypt_without_eof()

    test_valid_encrypt_decrypt()
    test_wrong_password()

