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


def save_array_as_image(arr, out_path):
    img = Image.fromarray(arr)
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


def to_grayscale(arr):
    from PIL import Image
    img = Image.fromarray(arr)
    return np.array(img.convert('L'), dtype=np.uint8)


def to_rgb(arr):
    from PIL import Image
    img = Image.fromarray(arr)
    return np.array(img.convert('RGB'), dtype=np.uint8)
