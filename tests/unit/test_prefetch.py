import json
import logging
from subprocess import CalledProcessError

import pytest

from pip2nix.errors import ReportError
from pip2nix.prefetch import prefetch_git, prefetch_url_path

from .urls import REPOSITORY


COMMIT = "a" * 40

ARCHIVE_URL = "https://index.example/certifi-2026.1.1.zip"

FAILURES = [
    FileNotFoundError("nix-prefetch-url"),
    CalledProcessError(1, "nix-prefetch-url"),
]


def reported(rev):
    payload = {"sha256": "the-content-hash", "rev": rev, "path": "/store/repo"}
    return json.dumps(payload).encode("utf-8")


@pytest.mark.parametrize("failure", FAILURES)
def test_reports_a_url_whose_path_it_cannot_prefetch(mocker, failure):
    mocker.patch("pip2nix.prefetch.check_output", side_effect=failure)

    with pytest.raises(ReportError):
        prefetch_url_path(ARCHIVE_URL, "ff" * 32)


@pytest.mark.parametrize("failure", FAILURES)
def test_reports_a_repository_it_cannot_prefetch(mocker, failure):
    mocker.patch("pip2nix.prefetch.check_output", side_effect=failure)

    with pytest.raises(ReportError):
        prefetch_git(f"https://git.example/{type(failure).__name__}", COMMIT)


def test_offers_a_known_hash_so_the_store_can_answer(mocker):
    check_output = mocker.patch(
        "pip2nix.prefetch.check_output", return_value=reported(rev=COMMIT)
    )

    prefetch_git(REPOSITORY, COMMIT, "the-recorded-hash")

    assert check_output.call_args.args[0] == [
        "nix-prefetch-git",
        REPOSITORY,
        COMMIT,
        "the-recorded-hash",
    ]


def test_offers_no_hash_when_none_was_recorded(mocker):
    check_output = mocker.patch(
        "pip2nix.prefetch.check_output", return_value=reported(rev=COMMIT)
    )

    prefetch_git(REPOSITORY, COMMIT)

    assert check_output.call_args.args[0] == ["nix-prefetch-git", REPOSITORY, COMMIT]


def test_keeps_the_commit_id_a_reused_store_path_does_not_report(mocker):
    mocker.patch("pip2nix.prefetch.check_output", return_value=reported(rev=""))

    _hash, commit_id, _path = prefetch_git(REPOSITORY, COMMIT, "the-recorded-hash")

    assert commit_id == COMMIT


def test_announces_a_repository_it_is_about_to_clone(mocker, caplog):
    caplog.set_level(logging.INFO)
    mocker.patch("pip2nix.prefetch.check_output", return_value=reported(rev=COMMIT))

    prefetch_git(REPOSITORY, COMMIT)

    assert REPOSITORY in caplog.text
    assert COMMIT in caplog.text


def test_says_nothing_when_a_recorded_hash_can_answer(mocker, caplog):
    caplog.set_level(logging.INFO)
    mocker.patch("pip2nix.prefetch.check_output", return_value=reported(rev=COMMIT))

    prefetch_git(REPOSITORY, COMMIT, "the-recorded-hash")

    assert not caplog.records


def test_announces_a_url_it_is_about_to_download(mocker, caplog):
    caplog.set_level(logging.INFO)
    mocker.patch("pip2nix.prefetch.check_output", return_value=b"/store/certifi")

    prefetch_url_path(ARCHIVE_URL, "ff" * 32)

    assert ARCHIVE_URL in caplog.text
