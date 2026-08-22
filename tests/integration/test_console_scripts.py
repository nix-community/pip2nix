"""
The guard for ADR-0007, which needs a real build to say anything.

Every supported interpreter is checked rather than one: the defect
this replaces was three builds agreeing on a name, which a
single-target test would not have caught.
"""

import os
import subprocess

import pytest


pytestmark = pytest.mark.nix

SUPPORTED = ["3.11", "3.12", "3.13", "3.14"]


@pytest.mark.parametrize("version", SUPPORTED)
def test_build_names_the_interpreter_it_resolves_against(version):
    assert installed_commands(build(version)) == [
        "pip2nix",
        f"pip2nix{version}",
    ]


def test_versioned_commands_reach_their_own_build_from_one_profile():
    builds = {version: build(version) for version in ("3.11", "3.13")}
    profile = build_profile(builds.values())

    reached = {
        version: os.path.realpath(os.path.join(profile, "bin", "pip2nix" + version))
        for version in builds
    }

    assert reached == {
        version: os.path.join(out_path, "bin", "pip2nix")
        for version, out_path in builds.items()
    }


def test_the_installed_command_reports_its_own_name():
    # `installed_commands` hides the dotfiles a wrapper leaves behind, so
    # the name a user sees is what says how often the command was wrapped.
    assert usage_line(build("3.13")).startswith("Usage: pip2nix ")


def build(version):
    return nix_build([".#pip2nix_python{}".format(version.replace(".", ""))])


def build_profile(out_paths):
    """
    The builds installed side by side, as a profile installs them.

    Collisions are ignored rather than absent: the unversioned command
    is in every build, and a profile resolves that by priority. The
    versioned names are what has to stay distinct.
    """
    paths = " ".join(f'(builtins.storePath "{path}")' for path in out_paths)
    return nix_build(
        [
            "--impure",
            "--expr",
            (
                'with import <nixpkgs> {}; buildEnv { name = "pip2nix-profile"; '
                f"ignoreCollisions = true; paths = [ {paths} ]; }}"
            ),
        ]
    )


def nix_build(arguments):
    return subprocess.run(
        ["nix", "build", "--no-link", "--print-out-paths"] + arguments,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def usage_line(out_path):
    return subprocess.run(
        [os.path.join(out_path, "bin", "pip2nix"), "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()[0]


def installed_commands(out_path):
    return sorted(
        name
        for name in os.listdir(os.path.join(out_path, "bin"))
        if not name.startswith(".")
    )
