import subprocess
import textwrap
from contextlib import chdir

import pytest
from click.testing import CliRunner
from packaging.utils import canonicalize_name

from pip2nix.cli import scaffold


pytestmark = pytest.mark.nix


@pytest.mark.parametrize("package", ["my-project", "My_Project", "2to3"])
def test_scaffolded_default_nix_evaluates(tmp_path, package):
    default_nix = run_scaffold(tmp_path, package)
    (tmp_path / "python-packages.nix").write_text(
        stub_package_set(canonicalize_name(package))
    )

    instantiate = subprocess.run(
        ["nix-instantiate", str(default_nix)], capture_output=True, text=True
    )

    assert instantiate.returncode == 0, instantiate.stderr


def run_scaffold(tmp_path, package):
    with chdir(tmp_path):
        result = CliRunner().invoke(scaffold, ["--package", package])
    assert result.exit_code == 0, result.output
    return tmp_path / "default.nix"


def stub_package_set(name):
    return textwrap.dedent("""\
        { pkgs, fetchurl, fetchgit, fetchhg }:

        self: super: {
          "PACKAGE" = super.buildPythonPackage {
            pname = "PACKAGE";
            version = "1.0";
            src = ./.;
            format = "setuptools";
          };
        }
    """).replace("PACKAGE", name)
