from contextlib import chdir

from click.testing import CliRunner

from pip2nix.cli import scaffold


def test_refers_to_the_package_by_its_canonical_name(tmp_path):
    with chdir(tmp_path):
        result = CliRunner().invoke(scaffold, ["--package", "My_Project"])

    assert result.exit_code == 0, result.output
    assert '"my-project" = super."my-project"' in (tmp_path / "default.nix").read_text()
