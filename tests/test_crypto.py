"""Tests for envoy.crypto encryption/decryption utilities."""

import pytest
from envoy.crypto import encrypt, decrypt


PASSPHRASE = "super-secret-passphrase-123"
SAMPLE_PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db\nSECRET_KEY=abc123"


def test_encrypt_returns_string():
    result = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_produces_different_ciphertexts():
    """Each encryption call should produce a unique ciphertext (random salt/nonce)."""
    result1 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    result2 = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    assert result1 != result2


def test_decrypt_roundtrip():
    encoded = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    decoded = decrypt(encoded, PASSPHRASE)
    assert decoded == SAMPLE_PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    encoded = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(encoded, "wrong-passphrase")


def test_decrypt_corrupted_payload_raises():
    encoded = encrypt(SAMPLE_PLAINTEXT, PASSPHRASE)
    corrupted = encoded[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid encoded payload"):
        decrypt("!!!not-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSPHRASE)


def test_encrypt_empty_string():
    encoded = encrypt("", PASSPHRASE)
    assert decrypt(encoded, PASSPHRASE) == ""


def test_encrypt_unicode_content():
    unicode_text = "KEY=héllo wörld 🔑"
    encoded = encrypt(unicode_text, PASSPHRASE)
    assert decrypt(encoded, PASSPHRASE) == unicode_text


@pytest.mark.parametrize("passphrase", [
    "short",
    "a" * 64,
    "passphrase with spaces and $peci@l ch@rs!",
])
def test_decrypt_roundtrip_various_passphrases(passphrase):
    """Encryption/decryption should work correctly for a range of passphrase formats."""
    encoded = encrypt(SAMPLE_PLAINTEXT, passphrase)
    assert decrypt(encoded, passphrase) == SAMPLE_PLAINTEXT
