from contextlib import chdir
from textwrap import dedent

import pytest

from pip2nix.models.package import source_to_nix
from pip2nix.models.source import Archive, FetchGit, FetchUrl, LocalPath

from .digests import SHA256_BASE32, SHA256_HEX
from .urls import CERTIFI, REPOSITORY


COMMIT = "a" * 40


def test_file_source(tmpdir):
    with chdir(tmpdir):
        source = LocalPath(url=f"file://{tmpdir}", path=str(tmpdir))
        assert source_to_nix(source) == "./."


def test_an_archive_renders_the_digest_it_was_given():
    source = FetchUrl(url=CERTIFI.wheel, sha256=SHA256_BASE32)

    assert source_to_nix(source) == dedent("""\
        fetchurl {
          url = "https://index.example/packages/certifi-2026.1.1-py3-none-any.whl";
          sha256 = "04mmsvw5c0ps2gh6hqwkcs5gyyvmfpr32zvxmv3w68a2mn5kwm39";
        }""")


def test_a_repository_renders_the_commit_id_and_hash_it_was_given():
    source = FetchGit(url=REPOSITORY, rev=COMMIT, sha256="the-content-hash")

    assert source_to_nix(source) == dedent(f"""\
        fetchgit {{
          url = "https://git.example/repo";
          rev = "{COMMIT}";
          sha256 = "the-content-hash";
        }}""")


def test_a_source_the_adapter_did_not_resolve_is_refused():
    """
    Falling through the match would render `src = None;`, and the file
    would still parse.
    """
    source = Archive(
        url=CERTIFI.wheel, path="/packages/certifi.whl", sha256_hex=SHA256_HEX
    )

    with pytest.raises(TypeError):
        source_to_nix(source)
