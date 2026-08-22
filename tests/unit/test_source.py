from unittest.mock import Mock

import pytest

from pip2nix.errors import UnresolvableRevision
from pip2nix.models.source import (
    Archive,
    FetchGit,
    FetchUrl,
    LocalPath,
    Repository,
    Source,
)

from ..doubles import sources
from .digests import SHA256_BASE32, SHA256_HEX
from .urls import CERTIFI, REPOSITORY


COMMIT = "a" * 40


def git_source(commit_id=COMMIT):
    return Repository(url=REPOSITORY, commit_id=commit_id)


def prefetching():
    return Mock(return_value=("the-content-hash", COMMIT, "/store/repo"))


@pytest.mark.parametrize(
    "commit_id",
    ["a" * 40, "A" * 40, "0123456789abcdef0123456789abcdef01234567"],
)
def test_a_repository_takes_a_commit_id_as_pip_reports_one(commit_id):
    assert Repository(url=REPOSITORY, commit_id=commit_id).commit_id == commit_id


@pytest.mark.parametrize(
    "commit_id",
    [None, "", "a" * 39, "a" * 41, "a" * 64, "main", "refs/heads/main"],
)
def test_a_repository_refuses_what_is_not_a_commit_id(commit_id):
    with pytest.raises(UnresolvableRevision):
        Repository(url=REPOSITORY, commit_id=commit_id)


def test_fetches_a_repository_once_however_often_it_is_asked():
    prefetch = prefetching()
    fetcher = sources(prefetch)

    fetcher.repository(git_source())
    fetcher.repository(git_source())

    prefetch.assert_called_once()


def test_hands_the_prefetch_the_hash_recorded_for_the_commit_id():
    prefetch = prefetching()
    fetcher = sources(prefetch, {(REPOSITORY, COMMIT): "the-recorded-hash"})

    fetcher.repository(git_source())

    prefetch.assert_called_once_with(REPOSITORY, COMMIT, "the-recorded-hash")


def test_hands_the_prefetch_no_hash_for_another_commit_id():
    prefetch = prefetching()
    fetcher = sources(prefetch, {(REPOSITORY, "b" * 40): "the-recorded-hash"})

    fetcher.repository(git_source())

    prefetch.assert_called_once_with(REPOSITORY, COMMIT, None)


def test_the_local_path_of_a_repository_is_its_checkout():
    fetcher = sources(prefetching())

    assert fetcher.local_path(git_source()) == "/store/repo"


def test_the_local_path_of_a_local_source_is_its_own():
    fetcher = sources()

    assert fetcher.local_path(LocalPath(url="file:///src", path="/src")) == "/src"


def test_the_local_path_of_an_archive_is_where_the_prefetch_put_it():
    prefetch = Mock(return_value="/store/certifi.tar.gz")
    fetcher = sources(prefetch_archive=prefetch)

    path = fetcher.local_path(
        Archive(
            url=CERTIFI.sdist,
            path="/packages/certifi-2026.1.1.tar.gz",
            sha256_hex=SHA256_HEX,
        )
    )

    prefetch.assert_called_once_with(CERTIFI.sdist, SHA256_HEX)
    assert path == "/store/certifi.tar.gz"


def test_resolving_a_repository_takes_the_commit_id_and_hash_it_fetched():
    fetcher = sources(prefetching())

    assert fetcher.resolved(git_source()) == FetchGit(
        url=REPOSITORY, rev=COMMIT, sha256="the-content-hash"
    )


def test_resolving_an_archive_re_encodes_the_digest_without_fetching():
    fetcher = sources()

    resolved = fetcher.resolved(
        Archive(
            url=CERTIFI.sdist,
            path="/packages/certifi-2026.1.1.tar.gz",
            sha256_hex=SHA256_HEX,
        )
    )

    assert resolved == FetchUrl(url=CERTIFI.sdist, sha256=SHA256_BASE32)


def test_resolving_a_local_source_leaves_it_as_it_is():
    source = LocalPath(url="file:///src", path="/src")

    assert sources().resolved(source) is source


def test_fetches_a_repository_once_although_both_passes_ask_for_it():
    """
    Resolving in the adapter must not double what a generation run
    clones.
    """
    prefetch = prefetching()
    fetcher = sources(prefetch)

    fetcher.local_path(git_source())
    fetcher.resolved(git_source())

    prefetch.assert_called_once()


@pytest.mark.parametrize("dispatcher", ["resolved", "local_path"])
def test_a_source_already_resolved_is_refused(dispatcher):
    fetcher = sources()
    resolved = FetchUrl(url=CERTIFI.sdist, sha256=SHA256_BASE32)

    with pytest.raises(TypeError):
        getattr(fetcher, dispatcher)(resolved)


def test_every_kind_is_one_a_dispatcher_answers_for():
    """
    The adapter matches on what the report describes and the renderer on
    what fetches it, with `LocalPath` in both because it needs no
    resolving. A new kind has to be added to a dispatcher, not only to
    this file.
    """
    reported = {Repository, Archive, LocalPath}
    fetched_with = {FetchGit, FetchUrl, LocalPath}

    assert leaf_kinds(Source) == reported | fetched_with


def leaf_kinds(cls):
    subclasses = cls.__subclasses__()
    if not subclasses:
        return {cls}
    return set().union(*(leaf_kinds(subclass) for subclass in subclasses))
