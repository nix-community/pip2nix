import os

import pytest

from pip2nix.config import Config, ValidationError


@pytest.fixture
def cwd():
    old_cwd = os.getcwd()
    yield os.chdir
    os.chdir(old_cwd)


def test_merging_configs():
    c = Config()
    c.merge_options({"optA": "A", "optB": "B"})
    c.merge_options({"optA": "A2"})
    assert c["optA"] == "A2"
    assert c["optB"] == "B"


def test_loading_requirements_from_cli():
    c = Config()
    c.merge_cli_options(
        {
            "specifiers": ["other_package"],
            "editables": ["."],
            "constraints": [],
            "requirements": ["requirements.txt"],
        }
    )
    assert c["pip2nix"]["requirements"] == [
        "other_package",
        "-e .",
        "-r requirements.txt",
    ]


def test_get_requirements():
    c = Config()
    c.merge_options(
        {"pip2nix": {"requirements": ["simple", "-rreqs.txt", "-e editable"]}}
    )
    assert list(c.get_requirements()) == [
        (None, "simple"),
        ("-r", "reqs.txt"),
        ("-e", "editable"),
    ]


def test_excludes_the_packaging_tools_by_default():
    c = Config()
    c.merge_options({"pip2nix": {"requirements": ["."]}})
    c.validate()

    assert c.excluded_packages == ["pip", "setuptools", "wheel"]


@pytest.mark.parametrize(
    "declaration",
    [
        {
            "pip2nix:package:psycopg2": {
                "additional_requirements": ["nix:pkgs.postgresql"]
            }
        },
        {
            "pip2nix": {
                "package": {
                    "psycopg2": {"additional_requirements": ["nix:pkgs.postgresql"]}
                }
            }
        },
    ],
    ids=["section_heading", "nested_section"],
)
def test_refuses_per_package_configuration(declaration):
    c = Config()
    c.merge_options({"pip2nix": {"requirements": ["."]}})
    c.merge_options(declaration)

    with pytest.raises(ValidationError) as error:
        c.validate()

    assert "[pip2nix:package:psycopg2]" in str(error.value)


def test_finding_config_file(tmpdir, cwd):
    subdir = tmpdir.mkdir("sub")
    subdir.join("pip2nix.ini").write("[default]\na = sub/pip2nix.ini\n")
    tmpdir.join("pip2nix.ini").write("[pip2nix]\na = ./pip2nix.ini\n")

    cwd(str(subdir))
    c = Config()
    c.find_and_load()

    assert c["pip2nix"]["a"] == "./pip2nix.ini"
