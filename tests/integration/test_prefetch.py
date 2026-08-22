import pytest

from pip2nix.prefetch import prefetch_git


pytestmark = pytest.mark.nix


def test_prefetch_git_fetches_the_commit_it_is_given(remote):
    feature = remote.sha("refs/heads/feature")

    _hash, commit_id, _checkout = prefetch_git(remote.url, feature)

    assert commit_id == feature


def test_prefetch_git_reuses_a_store_path_it_already_has(remote):
    feature = remote.sha("refs/heads/feature")
    hash, _commit_id, path = prefetch_git(remote.url, feature)

    reused = prefetch_git(remote.url, feature, hash)

    assert reused == (hash, feature, path)
