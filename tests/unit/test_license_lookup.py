import json
import logging
from subprocess import CalledProcessError, TimeoutExpired

import pytest

from pip2nix.errors import ReportError
from pip2nix.license_lookup import NIXPKGS_TIMEOUT_SECONDS, LicenseLookup


NOT_IN_THE_HAND_WRITTEN_MAP = "Frobnicate 1.0"
NIXPKGS_PATH = "/nix/store/00000000000000000000000000000000-nixpkgs"


def test_maps_a_license_the_hand_written_map_knows(mocker):
    nixpkgs_refusing_to_be_asked(mocker)

    assert LicenseLookup().attribute_for("GPLv3") == "gpl3"


def test_maps_a_license_by_its_spdx_identifier(mocker):
    nixpkgs_answering(mocker, {"gpl3Plus": {"spdxId": "gpl-3.0-or-later"}})

    assert LicenseLookup().attribute_for("GPL-3.0-or-later") == "gpl3Plus"


def test_maps_nothing_for_a_license_nixpkgs_does_not_know(mocker):
    nixpkgs_answering(mocker, {})

    assert LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP) is None


def test_asks_nixpkgs_once_however_often_it_is_queried(mocker):
    check_output = nixpkgs_answering(mocker, {})
    lookup = LicenseLookup()

    lookup.attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)
    lookup.attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)

    assert len(license_queries(check_output)) == 1


def test_shares_what_nixpkgs_answered_with_no_other_lookup(mocker):
    check_output = nixpkgs_answering(mocker, {})

    LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)
    LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)

    assert len(license_queries(check_output)) == 2


def test_asks_the_nixpkgs_that_resolved_rather_than_the_search_path(mocker):
    check_output = nixpkgs_answering(mocker, {})

    LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)

    assert "<nixpkgs>" not in expression_of(license_queries(check_output)[0])


def test_names_the_nixpkgs_it_asked(mocker, caplog):
    caplog.set_level(logging.INFO)
    nixpkgs_answering(mocker, {})

    LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)

    assert NIXPKGS_PATH in caplog.text


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError("nix-instantiate"),
        CalledProcessError(1, "nix-instantiate"),
        TimeoutExpired("nix-instantiate", NIXPKGS_TIMEOUT_SECONDS),
    ],
)
def test_reports_a_lookup_nixpkgs_cannot_answer(mocker, failure):
    mocker.patch("pip2nix.license_lookup.check_output", side_effect=failure)

    with pytest.raises(ReportError):
        LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)


def test_says_what_to_set_when_nixpkgs_does_not_answer_in_time(mocker):
    mocker.patch(
        "pip2nix.license_lookup.check_output",
        side_effect=TimeoutExpired("nix-instantiate", NIXPKGS_TIMEOUT_SECONDS),
    )

    with pytest.raises(ReportError, match="NIX_PATH"):
        LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)


def test_bounds_the_wait_on_a_nixpkgs_that_does_not_resolve(mocker):
    check_output = nixpkgs_answering(mocker, {})

    LicenseLookup().attribute_for(NOT_IN_THE_HAND_WRITTEN_MAP)

    assert all(
        call.kwargs["timeout"] == NIXPKGS_TIMEOUT_SECONDS
        for call in check_output.call_args_list
    )


def nixpkgs_answering(mocker, known):
    def answer(command, **kwargs):
        if expression_of(command) == "<nixpkgs>":
            return f"{NIXPKGS_PATH}\n".encode()
        return json.dumps(json.dumps(known)).encode("utf-8")

    return mocker.patch("pip2nix.license_lookup.check_output", side_effect=answer)


def license_queries(check_output):
    return [
        call.args[0]
        for call in check_output.call_args_list
        if expression_of(call.args[0]) != "<nixpkgs>"
    ]


def expression_of(command):
    return command[-1]


def nixpkgs_refusing_to_be_asked(mocker):
    return mocker.patch(
        "pip2nix.license_lookup.check_output",
        side_effect=AssertionError("Asked nixpkgs what it knows."),
    )
