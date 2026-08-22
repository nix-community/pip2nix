import json
from types import SimpleNamespace

import pytest
from packaging.version import Version

from pip2nix import resolver as resolver_module
from pip2nix.config import Config
from pip2nix.errors import ReportError
from pip2nix.resolver import MINIMUM_PIP_VERSION, Resolver, parse_pip_version


PYTHON = "/nix/store/stub-python/bin/python"

MATURIN = SimpleNamespace(name="maturin", version="1.14.1")


def test_asks_pip_to_resolve_the_requirements():
    config = make_config(["certifi"])

    argv = Resolver(PYTHON, config).argv()

    assert argv == [
        PYTHON,
        "-m",
        "pip",
        "install",
        "--dry-run",
        "--ignore-installed",
        "--quiet",
        "--index-url",
        "https://pypi.python.org/simple",
        "certifi",
    ]


def test_passes_each_requirement_as_its_own_argument():
    config = make_config(["certifi", "idna >= 2.5, < 4"])

    argv = Resolver(PYTHON, config).argv()

    assert argv[-2:] == ["certifi", "idna >= 2.5, < 4"]


def test_passes_requirements_files_and_constraints():
    config = make_config(["-r requirements.txt"], constraints=["constraints.txt"])

    argv = Resolver(PYTHON, config).argv()

    assert argv[-4:] == [
        "--constraint",
        "constraints.txt",
        "--requirement",
        "requirements.txt",
    ]


def test_passes_the_indexes():
    config = make_config(
        ["certifi"],
        index_url="https://index.example/simple",
        extra_index_url=["https://extra.example/simple"],
    )

    argv = Resolver(PYTHON, config).argv()

    assert "--index-url" in argv
    assert argv[argv.index("--index-url") + 1] == "https://index.example/simple"
    assert argv[argv.index("--extra-index-url") + 1] == ("https://extra.example/simple")


def test_disables_the_index_when_configured():
    config = make_config(["certifi"], no_index=True)

    argv = Resolver(PYTHON, config).argv()

    assert "--no-index" in argv
    assert "--index-url" not in argv


def test_rejects_an_editable_requirement():
    config = make_config(["-e ."])

    with pytest.raises(ReportError):
        Resolver(PYTHON, config).argv()


def test_asks_pip_for_the_source_of_one_package():
    argv = Resolver(PYTHON, make_config(["maturin"])).source_argv(MATURIN)

    assert argv == [
        PYTHON,
        "-m",
        "pip",
        "install",
        "--dry-run",
        "--ignore-installed",
        "--quiet",
        "--index-url",
        "https://pypi.python.org/simple",
        "--no-deps",
        "--no-binary",
        "maturin",
        "maturin==1.14.1",
    ]


def test_asks_for_no_requirement_but_the_pinned_one():
    """
    A pass carrying the configured requirements would resolve the whole set
    again, and every package it named would be refused a wheel.
    """
    config = make_config(["-r requirements.txt"], constraints=["constraints.txt"])

    argv = Resolver(PYTHON, config).source_argv(MATURIN)

    assert "--requirement" not in argv
    assert "--constraint" not in argv


def test_carries_the_indexes_into_a_source_pass():
    config = make_config(
        ["maturin"],
        index_url="https://index.example/simple",
        extra_index_url=["https://extra.example/simple"],
    )

    argv = Resolver(PYTHON, config).source_argv(MATURIN)

    assert argv[argv.index("--index-url") + 1] == "https://index.example/simple"
    assert argv[argv.index("--extra-index-url") + 1] == ("https://extra.example/simple")


def test_disables_the_index_in_a_source_pass_as_well():
    config = make_config(["maturin"], no_index=True)

    argv = Resolver(PYTHON, config).source_argv(MATURIN)

    assert "--no-index" in argv
    assert "--index-url" not in argv


def test_reads_the_version_pip_prints():
    output = "pip 25.3 from /nix/store/stub/pip (python 3.13)\n"

    assert parse_pip_version(output) == Version("25.3")


def test_rejects_a_pip_that_cannot_write_a_report(mocker):
    mocker.patch(
        "pip2nix.resolver.subprocess.check_output",
        return_value=b"pip 21.3.1 from /nix/store/stub/pip (python 3.9)\n",
    )

    with pytest.raises(ReportError) as error:
        Resolver(PYTHON, make_config(["certifi"])).check_version()

    assert "21.3.1" in str(error.value)
    assert MINIMUM_PIP_VERSION in str(error.value)


def test_rejects_output_that_carries_no_version(mocker):
    mocker.patch("pip2nix.resolver.subprocess.check_output", return_value=b"")

    with pytest.raises(ReportError):
        Resolver(PYTHON, make_config(["certifi"])).check_version()


def test_reads_the_report_pip_wrote_where_it_was_asked_to(mocker):
    """
    Nothing else knows the path: it lives for one pass, in a temporary
    directory the reader owns.
    """
    written = {"version": "1", "install": []}

    def write_report(argv):
        with open(argv[argv.index("--report") + 1], "w") as f:
            json.dump(written, f)

    check_call = mocker.patch(
        "pip2nix.resolver.subprocess.check_call", side_effect=write_report
    )

    assert resolver_module._read_report([PYTHON, "-m", "pip"]) == written
    assert check_call.call_args.args[0][:3] == [PYTHON, "-m", "pip"]


def make_config(requirements, **options):
    config = Config()
    config.merge_options({"pip2nix": dict(options, requirements=requirements)})
    config.validate()
    return config
