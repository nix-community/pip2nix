"""
Nix's own base32 encoding.

Nix uses a 32 character alphabet without `e`, `o`, `u` and `t`, and reads
the digest starting from its last group of five bits, so no stock
encoder produces the same string.

`nix hash convert` answers the same, and ADR-0017 records why this is
kept rather than shelling out to it.
"""

ALPHABET = "0123456789abcdfghijklmnpqrsvwxyz"

SHA256_BYTES = 32


def from_hex(digest):
    raw = bytes.fromhex(digest)
    if len(raw) != SHA256_BYTES:
        raise ValueError(
            f"Expected a sha256 digest of {SHA256_BYTES} bytes, got {len(raw)}."
        )
    length = (len(raw) * 8 - 1) // 5 + 1
    return "".join(_char_at(raw, position) for position in reversed(range(length)))


def _char_at(raw, position):
    bit = position * 5
    index, offset = divmod(bit, 8)
    value = raw[index] >> offset
    if index + 1 < len(raw):
        value |= raw[index + 1] << (8 - offset)
    return ALPHABET[value & 0x1F]
