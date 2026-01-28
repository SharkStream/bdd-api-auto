import os
import binascii
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding


iv_bytes = b'0123456789abcdef'  # 16 bytes IV for AES
default_key = "1234567890abcdef123456"

def encrypt(raw_text: str) -> str:
    secret_key = os.environ.get("ENCRYPTION_KEY", default_key)
    if not secret_key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    key_bytes = secret_key.encode('utf-8')
    if len(key_bytes) != 24:
        key_bytes = key_bytes.ljust(24, b'\0')[:24]
    
    plain_text_source = os.environ.get("TEXT")
    plain_text = plain_text_source if plain_text_source else raw_text

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plain_text.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
    encryptor = cipher.encryptor()

    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return binascii.hexlify(encrypted).decode('utf-8')

def decrypt(enc_text: str) -> str:
    secret_key = os.environ.get("ENCRYPTION_KEY", default_key)
    if not secret_key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    key_bytes = secret_key.encode('utf-8')
    if len(key_bytes) != 24:
        key_bytes = key_bytes.ljust(24, b'\0')[:24]
    
    plain_text_source = os.environ.get("TEXT")
    enc_text_to_decrypt = plain_text_source if plain_text_source else enc_text

    encrypted_bytes = binascii.unhexlify(enc_text_to_decrypt.encode('utf-8'))

    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_data = unpadder.update(padded_data) + unpadder.finalize()

    return decrypted_data.decode('utf-8')


if __name__ == "__main__":
    # For quick testing
    sample_text = "password123"
    encrypted = encrypt(sample_text)
    print(f"Encrypted: {encrypted}")
    decrypted = decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    print(encrypt("SuperSecretPassword!"))