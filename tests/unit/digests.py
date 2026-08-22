"""
One sha256 digest in both forms pip2nix has to bridge: the hex an index
publishes, and the base32 Nix expects.

`nix hash convert --hash-algo sha256 --to nix32` agrees on this pair.
"""

SHA256_HEX = "69543e8bad4221c3c7ae7d7f31f275757bff8a66936368e013fa0256f8d6b512"
SHA256_BASE32 = "04mmsvw5c0ps2gh6hqwkcs5gyyvmfpr32zvxmv3w68a2mn5kwm39"
