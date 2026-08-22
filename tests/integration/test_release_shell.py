"""
The release environment is exercised only at a release, which is where the 2018
one was found broken -- years after the package set it read had stopped
evaluating.

This runs the tools in between.
"""

import subprocess

import pytest


pytestmark = pytest.mark.nix

RELEASE_TOOLS = ["pyproject-build", "twine", "cog", "towncrier", "just", "uv"]


@pytest.mark.parametrize("tool", RELEASE_TOOLS)
def test_release_shell_provides(tool):
    result = in_release_shell([tool, "--help"])

    assert result.returncode == 0, result.stderr


def in_release_shell(command):
    return subprocess.run(
        ["nix", "develop", ".#release", "--command"] + command,
        capture_output=True,
        text=True,
    )
