import pytest

from pip2nix import nix_base32


# Reference pairs produced with
# `nix hash convert --hash-algo sha256 --to nix32 <digest>`.
MATURIN_SDIST_SHA256 = (
    "69543e8bad4221c3c7ae7d7f31f275757bff8a66936368e013fa0256f8d6b512"
)
MATURIN_SDIST_BASE32 = "04mmsvw5c0ps2gh6hqwkcs5gyyvmfpr32zvxmv3w68a2mn5kwm39"


@pytest.mark.parametrize(
    "digest, expected",
    [
        (MATURIN_SDIST_SHA256, MATURIN_SDIST_BASE32),
        ("00" * 32, "0" * 52),
        ("ff" * 32, "1" + "z" * 51),
    ],
)
def test_encodes_a_known_digest(digest, expected):
    assert nix_base32.from_hex(digest) == expected


def test_accepts_upper_case_hex():
    assert nix_base32.from_hex(MATURIN_SDIST_SHA256.upper()) == MATURIN_SDIST_BASE32


def test_rejects_a_truncated_digest():
    with pytest.raises(ValueError):
        nix_base32.from_hex(MATURIN_SDIST_SHA256[:32])


def test_rejects_a_non_hex_digest():
    with pytest.raises(ValueError):
        nix_base32.from_hex("z" * 64)
