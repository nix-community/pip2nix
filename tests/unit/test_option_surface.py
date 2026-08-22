"""
The claims the configuration surface makes about itself.

Every option this repository has found accepted-and-ignored was found by
accident. These guard the shapes it came in: a key declared and read by
nothing, and a command-line default that quietly overwrites what a
configuration file said.
"""

import importlib
import inspect
import io

import configobj
import pytest
from click.testing import CliRunner

from pip2nix import resources
from pip2nix.cli import generate
from pip2nix.config import MERGED_CLI_OPTIONS, Config


# What reads each key `confspec.ini` declares, named down to the
# function so that naming one is a claim rather than a gesture. A key
# with no reader is the defect this repository keeps producing --
# `--no-binary`, `-e` and the `[[package]]` section were each found by
# accident rather than by looking.
KEY_READERS = {
    "requirements": "pip2nix.config:Config.get_requirements",
    "constraints": "pip2nix.config:Config.constraints",
    "index_url": "pip2nix.config:Config.indexes",
    "extra_index_url": "pip2nix.config:Config.indexes",
    "no_index": "pip2nix.config:Config.indexes",
    "only_direct": "pip2nix.config:Config.only_direct",
    "excluded_packages": "pip2nix.config:Config.excluded_packages",
    "output": "pip2nix.config:Config.output",
    "licenses": "pip2nix.config:Config.licenses",
}


FILE_VALUES = {
    "output": "./generated.nix",
    "index_url": "https://mirror.example/simple",
    "extra_index_url": [
        "https://internal.example/simple",
        "https://vendor.example/simple",
    ],
    "no_index": True,
    "only_direct": True,
    "licenses": True,
}


def test_the_fixture_covers_every_shared_option():
    assert set(FILE_VALUES) == set(MERGED_CLI_OPTIONS)


def test_every_shared_option_can_be_set_in_a_configuration_file(mocker):
    config = configuration_from_a_file_alone(mocker)

    assert {key: config["pip2nix"][key] for key in FILE_VALUES} == FILE_VALUES


def test_every_declared_key_is_named_by_a_reader():
    assert set(declared_keys()) == set(KEY_READERS)


@pytest.mark.parametrize("key,reader", sorted(KEY_READERS.items()))
def test_the_named_reader_reads_the_key(key, reader):
    source = source_of(reader)

    assert f'"{key}"' in source or f"'{key}'" in source


@pytest.mark.parametrize(
    "key", ["requirements", "constraints", "excluded_packages", "extra_index_url"]
)
def test_a_list_option_takes_a_single_value(key):
    config = Config()
    config.merge_options({"pip2nix": {"requirements": ["."], key: "one"}})

    config.validate()

    assert config["pip2nix"][key] == ["one"]


def declared_keys():
    spec = configobj.ConfigObj(
        {}, configspec=io.StringIO(resources.read_text("confspec.ini"))
    )
    return spec.configspec["pip2nix"].scalars


def source_of(reader):
    module_name, _, attributes = reader.partition(":")
    target = importlib.import_module(module_name)
    for attribute in attributes.split("."):
        target = getattr(target, attribute)
    for wrapper in ("callback", "fget"):
        target = getattr(target, wrapper, target)
    return inspect.getsource(target)


def configuration_from_a_file_alone(mocker):
    """
    The configuration `generate` builds when a file is the only source, every
    option being left at its command-line default.
    """
    resolve_packages = mocker.patch("pip2nix.cli.resolve_packages", return_value=[])
    mocker.patch("pip2nix.cli.write_output")

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("pip2nix.ini", "w") as configuration:
            configuration.write(as_ini(FILE_VALUES))
        runner.invoke(generate, [], catch_exceptions=False)

    return resolve_packages.call_args.args[0].config


def as_ini(values):
    lines = ["[pip2nix]", "requirements = ."]
    lines.extend(
        f"{key} = {as_ini_value(value)}" for key, value in sorted(values.items())
    )
    return "\n".join(lines) + "\n"


def as_ini_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(value)
    return value
