import os
import struct
import numpy as np
import cv2
from reedsolo import RSCodec, ReedSolomonError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Core Constants
MAGIC_BYTES = b"RSTG"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 100_000

# Fixed-Step QIM Parameters
BLOCK_SIZE = 8           # 8x8 macro blocks
STEP = 4.0               # Micro-step size for maximum compression tolerance
ECC_PARITY_BYTES = 32    # Reed-Solomon parity bytes

HEADER_SIZE_BITS = 16    # 2 bytes header storing payload length in bits
MAX_IMAGE_DIM = 1600     # Maximum dimension to prevent messaging app downsampling


class StegoError(Exception):
    """Generic exception to maintain plausible deniability."""
    pass


def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
    """Derive AES key and CSPRNG seed using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE + 32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key_material = kdf.derive(passphrase.encode('utf-8'))
    return key_material[:KEY_SIZE], key_material[KEY_SIZE:]


def derive_seed_only(passphrase: str) -> bytes:
    """Derive a deterministic PRNG seed directly from passphrase for index shuffling."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"STEGO_INDEX_SALT",
        iterations=10_000,
    )
    return kdf.derive(passphrase.encode('utf-8'))


class AES_CTR_CSPRNG:
    """CSPRNG using AES-256 in CTR mode to deterministically shuffle block indices."""
    def __init__(self, key: bytes):
        nonce = b'\x00' * 16
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        self.encryptor = cipher.encryptor()

    def generate_indices(self, total_blocks: int, required_count: int) -> np.ndarray:
        indices = np.arange(total_blocks, dtype=np.int32)
        bytes_needed = total_blocks * 4
        
        # Generate raw stream in exact chunks needed
        chunk = b""
        while len(chunk) < bytes_needed:
            chunk += self.encryptor.update(b'\x00' * 4096)
        
        # Perform Fisher-Yates shuffle deterministically
        for i in range(total_blocks - 1, 0, -1):
            offset = (total_blocks - 1 - i) * 4
            rand_int = struct.unpack(">I", chunk[offset:offset+4])[0]
            j = rand_int % (i + 1)
            indices[i], indices[j] = indices[j], indices[i]
            
        return indices[:required_count]


def apply_ecc(data: bytes) -> bytes:
    """Apply Reed-Solomon error correction encoding."""
    rs = RSCodec(ECC_PARITY_BYTES)
    return bytes(rs.encode(data))


def remove_ecc(encoded_data: bytes) -> bytes:
    """Decode Reed-Solomon ECC and correct errors from lossy compression."""
    rs = RSCodec(ECC_PARITY_BYTES)
    try:
        dec, _, _ = rs.decode(encoded_data)
        return bytes(dec)
    except ReedSolomonError:
        raise StegoError("Error: Could not extract any valid data with that passphrase")


def bytes_to_bits(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def bits_to_bytes(bits: np.ndarray) -> bytes:
    return np.packbits(bits).tobytes()


def embed_data(image_path: str, payload_text: str, passphrase: str, output_path: str):
    """Embed payload text using Fixed-Step Spatial QIM with automatic pre-resizing."""
    payload_bytes = payload_text.encode('utf-8')
    if len(payload_bytes) > 256:
        raise ValueError("Payload too large. Max size is 256 bytes.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    aes_key, _ = derive_keys(passphrase, salt)

    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, payload_bytes, None)

    framed_payload = MAGIC_BYTES + salt + nonce + ciphertext
    ecc_payload = apply_ecc(framed_payload)
    
    payload_bits = bytes_to_bits(ecc_payload)
    total_bit_len = len(payload_bits)
    header_bits = bytes_to_bits(struct.pack(">H", total_bit_len))
    full_bit_stream = np.concatenate([header_bits, payload_bits])

    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to load source image file.")

    # Auto-resize high-res images to safe app dimensions BEFORE embedding
    h, w = img.shape[:2]
    if max(h, w) > MAX_IMAGE_DIM:
        scale = MAX_IMAGE_DIM / float(max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)

    h, w = y_channel.shape
    num_blocks_h = h // BLOCK_SIZE
    num_blocks_w = w // BLOCK_SIZE
    total_blocks = num_blocks_h * num_blocks_w

    if total_blocks < len(full_bit_stream):
        raise ValueError("Image is too small to embed the requested payload.")

    prng_seed = derive_seed_only(passphrase)
    csprng = AES_CTR_CSPRNG(prng_seed)
    block_indices = csprng.generate_indices(total_blocks, len(full_bit_stream))

    for idx, bit in zip(block_indices, full_bit_stream):
        bh = (idx // num_blocks_w) * BLOCK_SIZE
        bw = (idx % num_blocks_w) * BLOCK_SIZE

        block = y_channel[bh:bh+BLOCK_SIZE, bw:bw+BLOCK_SIZE]
        avg_val = np.mean(block)

        # Fixed-Step QIM Modulation
        q_idx = round(avg_val / STEP)
        if q_idx % 2 != bit:
            q_idx += 1 if (avg_val >= q_idx * STEP) else -1

        target_avg = q_idx * STEP
        diff = target_avg - avg_val
        y_channel[bh:bh+BLOCK_SIZE, bw:bw+BLOCK_SIZE] = np.clip(block + diff, 0, 255)

    ycrcb[:, :, 0] = np.clip(y_channel, 0, 255).astype(np.uint8)
    final_img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

    cv2.imwrite(output_path, final_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])


def extract_data(image_path: str, passphrase: str) -> str:
    """Extract payload text using Fixed-Step QIM parity decoding."""
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise StegoError("Error: Could not extract any valid data with that passphrase")

    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)

    h, w = y_channel.shape
    num_blocks_h = h // BLOCK_SIZE
    num_blocks_w = w // BLOCK_SIZE
    total_blocks = num_blocks_h * num_blocks_w

    if total_blocks < HEADER_SIZE_BITS:
        raise StegoError("Error: Could not extract any valid data with that passphrase")

    prng_seed = derive_seed_only(passphrase)
    csprng = AES_CTR_CSPRNG(prng_seed)

    # 1. Read maximum possible sequence to inspect header deterministically
    max_possible_bits = min(total_blocks, HEADER_SIZE_BITS + 4096)
    indices = csprng.generate_indices(total_blocks, max_possible_bits)

    # Extract header bits (first 16 bits)
    header_bits = []
    for idx in indices[:HEADER_SIZE_BITS]:
        bh = (idx // num_blocks_w) * BLOCK_SIZE
        bw = (idx % num_blocks_w) * BLOCK_SIZE
        block = y_channel[bh:bh+BLOCK_SIZE, bw:bw+BLOCK_SIZE]
        avg_val = np.mean(block)
        
        q_idx = round(avg_val / STEP)
        header_bits.append(int(q_idx % 2))

    header_bytes = bits_to_bytes(np.array(header_bits, dtype=np.uint8))
    payload_bit_len = struct.unpack(">H", header_bytes)[0]

    if payload_bit_len <= 0 or (HEADER_SIZE_BITS + payload_bit_len) > total_blocks:
        raise StegoError("Error: Could not extract any valid data with that passphrase")

    # 2. Extract payload bits using exact contiguous indices sequence
    payload_bits = []
    for idx in indices[HEADER_SIZE_BITS:HEADER_SIZE_BITS + payload_bit_len]:
        bh = (idx // num_blocks_w) * BLOCK_SIZE
        bw = (idx % num_blocks_w) * BLOCK_SIZE
        block = y_channel[bh:bh+BLOCK_SIZE, bw:bw+BLOCK_SIZE]
        avg_val = np.mean(block)
        
        q_idx = round(avg_val / STEP)
        payload_bits.append(int(q_idx % 2))

    raw_ecc_bytes = bits_to_bytes(np.array(payload_bits, dtype=np.uint8))

    try:
        raw_payload = remove_ecc(raw_ecc_bytes)
        min_expected = len(MAGIC_BYTES) + SALT_SIZE + NONCE_SIZE
        if len(raw_payload) < min_expected:
            raise StegoError("Error: Could not extract any valid data with that passphrase")

        magic = raw_payload[:4]
        if magic != MAGIC_BYTES:
            raise StegoError("Error: Could not extract any valid data with that passphrase")

        salt = raw_payload[4:4+SALT_SIZE]
        nonce = raw_payload[4+SALT_SIZE:4+SALT_SIZE+NONCE_SIZE]
        ciphertext = raw_payload[4+SALT_SIZE+NONCE_SIZE:]

        aes_key, _ = derive_keys(passphrase, salt)
        aesgcm = AESGCM(aes_key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode('utf-8')
    except Exception:
        raise StegoError("Error: Could not extract any valid data with that passphrase")
