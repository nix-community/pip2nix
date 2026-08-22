import pytest

from pip2nix.models.license import license_expression_members

from ..doubles import nix_licenses


@pytest.fixture
def known_licenses():
    """
    Stands in for the `nixpkgs.lib.licenses` lookup, which needs nix.
    """
    return nix_licenses(
        {
            "Apache-2.0": "asl20",
            "BSD-2-Clause": "bsd2",
            "GPL-3.0-or-later": "gpl3Plus",
            "MIT": "mit",
            "MIT License": "mit",
        }
    )


def test_renders_nothing_when_no_license_is_declared(known_licenses):
    assert known_licenses.to_nix([], "certifi") is None


def test_renders_a_license_nixpkgs_knows(known_licenses):
    assert (
        known_licenses.to_nix(["GPL-3.0-or-later"], "certifi")
        == "[ pkgs.lib.licenses.gpl3Plus ]"
    )


def test_renders_only_the_spellings_nixpkgs_knows(known_licenses):
    assert (
        known_licenses.to_nix(["Frobnicate 1.0", "MIT"], "certifi")
        == "[ pkgs.lib.licenses.mit ]"
    )


def test_renders_each_license_once(known_licenses):
    assert (
        known_licenses.to_nix(["MIT", "MIT License"], "certifi")
        == "[ pkgs.lib.licenses.mit ]"
    )


def test_renders_the_first_license_by_name_when_nixpkgs_knows_none(known_licenses):
    assert (
        known_licenses.to_nix(["Frobnicate 1.0", "Frobnicate 2.0"], "certifi")
        == '[ { fullName = "Frobnicate 1.0"; } ]'
    )


def test_resolves_an_expression_into_the_attributes_it_names(known_licenses):
    assert (
        known_licenses.to_nix(["Apache-2.0 OR BSD-2-Clause"], "certifi")
        == "[ pkgs.lib.licenses.asl20 pkgs.lib.licenses.bsd2 ]"
    )


def test_keeps_an_expression_whole_when_nixpkgs_misses_one_member(known_licenses):
    assert (
        known_licenses.to_nix(["MIT OR Zlib"], "certifi")
        == '[ { fullName = "MIT OR Zlib"; } ]'
    )


def test_keeps_an_expression_that_has_no_list_form(known_licenses):
    declared = "GPL-2.0-or-later WITH Bison-exception-2.2"

    assert (
        known_licenses.to_nix([declared], "certifi")
        == f'[ {{ fullName = "{declared}"; }} ]'
    )


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ('A "quoted" license', r'{ fullName = "A \"quoted\" license"; }'),
        (r"A back\slash license", r'{ fullName = "A back\\slash license"; }'),
        ("${pkgs.hello} license", r'{ fullName = "\${pkgs.hello} license"; }'),
    ],
)
def test_escapes_a_full_name_that_would_end_the_nix_string(
    known_licenses, declared, expected
):
    assert known_licenses.to_nix([declared], "certifi") == f"[ {expected} ]"


def test_warns_about_the_members_that_kept_a_license_as_a_full_name(
    known_licenses, caplog
):
    known_licenses.to_nix(["MIT OR Zlib"], "certifi")

    assert "certifi" in caplog.text
    assert "Zlib" in caplog.text


def test_says_nothing_when_nixpkgs_knows_the_license(known_licenses, caplog):
    known_licenses.to_nix(["MIT"], "certifi")

    assert not caplog.records


def test_names_the_licenses_an_expression_carries():
    assert license_expression_members("Apache-2.0 OR BSD-2-Clause") == [
        "Apache-2.0",
        "BSD-2-Clause",
    ]


def test_names_the_licenses_of_an_expression_in_canonical_spelling():
    assert license_expression_members("apache-2.0 and mit") == ["Apache-2.0", "MIT"]


def test_names_the_one_license_a_bare_identifier_carries():
    assert license_expression_members("MIT") == ["MIT"]


@pytest.mark.parametrize(
    "expression",
    [
        "GPL-2.0-or-later WITH Bison-exception-2.2",
        "(MIT OR Apache-2.0) AND BSD-3-Clause",
    ],
)
def test_names_nothing_for_an_expression_with_no_list_form(expression):
    assert license_expression_members(expression) is None


def test_names_nothing_for_what_is_not_an_expression():
    assert license_expression_members("Frobnicate 1.0") is None
