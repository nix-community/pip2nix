from textwrap import dedent

from click.testing import CliRunner

from pip2nix.cli import generate
from pip2nix.errors import ReportError, UnresolvableRevision

from ..doubles import resolver


PACKAGE_CONFIGURATION = dedent("""\
    [pip2nix]
    requirements = .

    [pip2nix:package:pip2nix:args]
    makeWrapperArgs = '"--prefix PATH : ${pkgs.nix-prefetch-scripts}"'
""")

MALFORMED_REQUIREMENT = "not a requirement!"

COMMIT = "65486e4383f9f411da95937451205d3c7b61b9e1"

CANNOT_FETCH_THE_SOURCE = "Cannot fetch https://index.example/certifi-2026.1.1.tar.gz."

UNRESOLVABLE_REVISION = (
    'Cannot resolve "1.16.0" to a commit in https://git.example/six.'
)

REPORT_WITH_A_GIT_SOURCE = {
    "version": "1",
    "environment": {"python_version": "3.13", "sys_platform": "linux"},
    "install": [
        {
            "requested": True,
            "metadata": {"name": "six", "version": "1.16.0"},
            "download_info": {
                "url": "https://git.example/six",
                "vcs_info": {
                    "vcs": "git",
                    "requested_revision": "1.16.0",
                    "commit_id": COMMIT,
                },
            },
        }
    ],
}

REPORT_WITH_A_WHEEL = {
    "version": "1",
    "environment": {"python_version": "3.13", "sys_platform": "linux"},
    "install": [
        {
            "requested": True,
            "metadata": {"name": "certifi", "version": "2026.1.1"},
            "download_info": {
                "url": "https://index.example/certifi-2026.1.1-py3-none-any.whl",
                "archive_info": {"hashes": {"sha256": "ff" * 32}},
            },
        }
    ],
}

REPORT_WITH_A_LICENSED_WHEEL = {
    "version": "1",
    "environment": {"python_version": "3.13", "sys_platform": "linux"},
    "install": [
        {
            "requested": True,
            "metadata": {
                "name": "certifi",
                "version": "2026.1.1",
                "license_expression": "GPL-3.0-or-later",
            },
            "download_info": {
                "url": "https://index.example/certifi-2026.1.1-py3-none-any.whl",
                "archive_info": {"hashes": {"sha256": "ff" * 32}},
            },
        }
    ],
}

REPORT_WITH_A_MALFORMED_REQUIREMENT = {
    "version": "1",
    "environment": {"python_version": "3.13", "sys_platform": "linux"},
    "install": [
        {
            "requested": True,
            "metadata": {
                "name": "trytond",
                "version": "7.0.0",
                "requires_dist": [MALFORMED_REQUIREMENT],
            },
        }
    ],
}


def test_rejects_an_editable_requirement_on_the_command_line(mocker):
    mocker.patch("pip2nix.resolver.Resolver.check_version")
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["-e", "."])

    assert "Editable requirements are not supported" in result.output


def test_rejects_per_package_configuration_from_the_ini_file():
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open("pip2nix.ini", "w") as configuration:
            configuration.write(PACKAGE_CONFIGURATION)
        result = runner.invoke(generate, [])

    assert "[pip2nix:package:pip2nix]" in result.output


def test_reports_a_malformed_requirement_the_report_carries(mocker):
    mocker.patch(
        "pip2nix.cli.Resolver",
        return_value=resolver(resolve=lambda: REPORT_WITH_A_MALFORMED_REQUIREMENT),
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["trytond"])

    assert result.exit_code == 1
    assert "trytond" in result.output
    assert MALFORMED_REQUIREMENT in result.output


def test_reports_a_failure_that_only_rendering_reaches(mocker):
    mocker.patch(
        "pip2nix.cli.Resolver",
        return_value=resolver(resolve=lambda: REPORT_WITH_A_WHEEL),
    )
    mocker.patch(
        "pip2nix.cli.write_output", side_effect=ReportError(CANNOT_FETCH_THE_SOURCE)
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["certifi"])

    assert result.exit_code == 1
    assert CANNOT_FETCH_THE_SOURCE in result.output


def test_reports_a_revision_it_cannot_resolve(mocker):
    mocker.patch(
        "pip2nix.cli.Resolver",
        return_value=resolver(resolve=lambda: REPORT_WITH_A_GIT_SOURCE),
    )
    mocker.patch(
        "pip2nix.cli.prefetch_git",
        side_effect=UnresolvableRevision(UNRESOLVABLE_REVISION),
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["six"])

    assert result.exit_code == 1
    assert UNRESOLVABLE_REVISION in result.output


def test_writes_the_license_it_was_asked_for(mocker):
    mocker.patch(
        "pip2nix.cli.Resolver",
        return_value=resolver(resolve=lambda: REPORT_WITH_A_LICENSED_WHEEL),
    )
    mocker.patch("pip2nix.cli.LicenseLookup.attribute_for", return_value="gpl3Plus")
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["--licenses", "certifi"])
        assert result.exit_code == 0, result.output
        with open("python-packages.nix") as generated:
            content = generated.read()

    assert "license = [ pkgs.lib.licenses.gpl3Plus ];" in content


def test_asks_nixpkgs_nothing_when_no_license_was_asked_for(mocker):
    mocker.patch(
        "pip2nix.cli.Resolver",
        return_value=resolver(resolve=lambda: REPORT_WITH_A_LICENSED_WHEEL),
    )
    mocker.patch(
        "pip2nix.cli.LicenseLookup",
        side_effect=AssertionError("Built a lookup to ask nixpkgs with."),
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(generate, ["certifi"])
        assert result.exit_code == 0, result.output
        with open("python-packages.nix") as generated:
            content = generated.read()

    assert "meta" not in content
