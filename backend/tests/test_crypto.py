from app.utils.crypto import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    plaintext = "s3cret-pass!"
    token = encrypt(plaintext)
    assert token != plaintext
    assert decrypt(token) == plaintext


def test_decrypt_none_returns_none():
    assert decrypt(None) is None
