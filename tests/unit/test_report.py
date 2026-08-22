import json
import os
from dataclasses import FrozenInstanceError
from textwrap import dedent
from unittest.mock import Mock

import pytest

from pip2nix.errors import ReportError
from pip2nix.models.license import NoLicenses
from pip2nix.models.package import PYPROJECT, SETUPTOOLS, WHEEL
from pip2nix.models.source import Archive, LocalPath, Repository
from pip2nix.report import (
    needs_source_distribution,
    packages_from_report,
    read_build_systems,
    resolve_source_distributions,
    resolve_sources,
    source_distribution_of,
)

from ..doubles import resolver, sources
from .urls import CERTIFI


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

ENVIRONMENT = {"sys_platform": "linux", "python_version": "3.13"}


@pytest.fixture
def report():
    return load_report("report-single-wheel.json")


@pytest.fixture
def trytond_report():
    """
    A real report for `trytond_account` as pip wrote it.

    It carries extras, markers and names that are not canonical.
    """
    return load_report("report-trytond-account.json")


@pytest.fixture
def git_report():
    """
    A real report for `six` installed from its git repository, captured by
    `fixtures/capture-reports.sh`.
    """
    return load_report("report-git.json")


@pytest.fixture
def binary_wheel_report():
    """
    A real report for `asyncpg`, which pip resolves to a manylinux wheel that
    Nix cannot build from.
    """
    return load_report("report-binary-wheel.json")


@pytest.fixture
def sdist_report():
    """
    The same requirement resolved once the wheel is refused, which is what the
    substitution of ADR-0003 takes its source from.
    """
    return load_report("report-binary-wheel-sdist.json")


@pytest.fixture
def setuptools_report():
    """
    A real report for `zc.lockfile`, which declares `setuptools` at runtime, so
    the resolution carries it as a package and as an edge.
    """
    return load_report("report-setuptools.json")


@pytest.fixture
def source_passes():
    """
    A resolver answering every pass with the source distribution of the package
    it was asked for, and recording every package it was asked for.
    """

    def source_of(package):
        return one_package_report(
            package.name, package.version, f"{package.name}-{package.version}.tar.gz"
        )

    return resolver(resolve_source=Mock(side_effect=source_of))


def packages_of(passes):
    return [call.args[0].name for call in passes.resolve_source.call_args_list]


def load_report(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def one_package_report(name, version, filename):
    return {
        "version": "1",
        "environment": ENVIRONMENT,
        "install": [
            {
                "requested": True,
                "metadata": {"name": name, "version": version},
                "download_info": {
                    "url": "https://index.example/packages/" + filename,
                    "archive_info": {"hashes": {"sha256": "ff" * 32}},
                },
            }
        ],
    }


def maturin_report():
    """
    Maturin as pip resolves it, which is the case ADR-0005 turns on: it is
    emitted as a package and builds two others in the same run.
    """
    return one_package_report(
        "maturin", "1.14.1", "maturin-1.14.1-py3-none-manylinux_2_12_x86_64.whl"
    )


def package_named(packages, name):
    return next(package for package in packages if package.name == name)


def test_renders_a_wheel_from_the_report(report):
    packages = read_build_systems(packages_from_report(report), ENVIRONMENT, sources())
    packages = resolve_sources(packages, sources())

    assert len(packages) == 1
    assert packages[0].to_nix(NoLicenses()) == dedent("""\
        super.buildPythonPackage rec {
          pname = "certifi";
          version = "2026.1.1";
          src = fetchurl {
            url = "https://index.example/packages/certifi-2026.1.1-py3-none-any.whl";
            sha256 = "04mmsvw5c0ps2gh6hqwkcs5gyyvmfpr32zvxmv3w68a2mn5kwm39";
          };
          format = "wheel";
          doCheck = false;
          buildInputs = [];
          nativeBuildInputs = [];
          propagatedBuildInputs = [];
        };""")


def test_names_a_package_canonically(report):
    report["install"][0]["metadata"]["name"] = "Trytond_Account"

    assert packages_from_report(report)[0].name == "trytond-account"


def test_reads_the_dependencies_of_a_package(trytond_report):
    expected = [
        ("python-dateutil", "2.9.0.post0"),
        ("python-sql", "1.8.1"),
        ("simpleeval", "1.0.7"),
        ("trytond", "7.0.55"),
        ("trytond-company", "7.0.4"),
        ("trytond-currency", "7.0.1"),
        ("trytond-party", "7.0.7"),
    ]

    packages = packages_from_report(trytond_report)

    assert package_named(packages, "trytond-account").dependencies == expected


def test_renders_a_dependency_an_extra_pulled_in(trytond_report):
    expected = dedent("""\
        propagatedBuildInputs = [
            self."genshi"
            self."lxml"
            self."puremagic"
          ];""")

    packages = resolve_sources(packages_from_report(trytond_report), sources())

    assert expected in package_named(packages, "relatorio").to_nix(NoLicenses())


def test_reads_no_dependencies_when_every_requirement_is_extra_gated(trytond_report):
    packages = packages_from_report(trytond_report)

    assert package_named(packages, "lxml").dependencies == []


def test_emits_only_the_requested_packages(trytond_report):
    packages = packages_from_report(trytond_report, only_direct=True)

    assert [package.name for package in packages] == ["trytond-account"]


def test_keeps_the_dependencies_on_packages_it_does_not_emit(trytond_report):
    expected = [
        "python-dateutil",
        "python-sql",
        "simpleeval",
        "trytond",
        "trytond-company",
        "trytond-currency",
        "trytond-party",
    ]

    packages = packages_from_report(trytond_report, only_direct=True)

    package = package_named(packages, "trytond-account")
    assert [name for name, _version in package.dependencies] == expected


def test_emits_every_resolved_package_by_default(trytond_report):
    packages = packages_from_report(trytond_report)

    assert len(packages) == len(trytond_report["install"])


def test_omits_an_excluded_package(setuptools_report):
    packages = packages_from_report(setuptools_report, excluded=["setuptools"])

    assert [package.name for package in packages] == ["zc-lockfile"]


def test_drops_the_edges_to_an_excluded_package(setuptools_report):
    packages = packages_from_report(setuptools_report, excluded=["setuptools"])

    assert package_named(packages, "zc-lockfile").dependencies == []


@pytest.mark.parametrize("spelling", ["zc.lockfile", "ZC_Lockfile"])
def test_matches_an_excluded_name_canonically(setuptools_report, spelling):
    packages = packages_from_report(setuptools_report, excluded=[spelling])

    assert [package.name for package in packages] == ["setuptools"]


def test_omits_an_excluded_package_that_was_requested(setuptools_report):
    packages = packages_from_report(
        setuptools_report, only_direct=True, excluded=["zc.lockfile"]
    )

    assert packages == []


@pytest.mark.parametrize(
    "filename, needed",
    [
        ("certifi-2026.1.1-py3-none-any.whl", False),
        ("certifi-2026.1.1-py2.py3-none-any.whl", False),
        ("asyncpg-0.30.0-cp313-cp313-manylinux_2_17_x86_64.whl", True),
        ("certifi-2026.1.1.tar.gz", False),
        ("certifi-2026.1.1.zip", False),
        ("certifi-2026.1.1-py3.13.egg", True),
    ],
)
def test_which_sources_nix_cannot_build_from(filename, needed):
    source = Archive(
        url="https://index.example/packages/" + filename,
        path="/packages/" + filename,
        sha256_hex="ab" * 32,
    )

    assert needs_source_distribution(source) is needed


def test_a_repository_needs_no_source_distribution():
    source = Repository(url="https://git.example/repo", commit_id="a" * 40)

    assert needs_source_distribution(source) is False


def test_takes_the_source_distribution_of_a_binary_wheel(
    binary_wheel_report, sdist_report
):
    package = packages_from_report(binary_wheel_report)[0]

    source = source_distribution_of(package, sdist_report)

    assert source.url.endswith("asyncpg-0.30.0.tar.gz")


def test_pins_the_substituted_source_to_its_own_hash(binary_wheel_report, sdist_report):
    expected = sdist_report["install"][0]["download_info"]["archive_info"]["hashes"][
        "sha256"
    ]
    package = packages_from_report(binary_wheel_report)[0]

    assert source_distribution_of(package, sdist_report).sha256_hex == expected


def test_rejects_a_source_distribution_of_another_version(
    binary_wheel_report, sdist_report
):
    sdist_report["install"][0]["metadata"]["version"] = "0.31.0"
    package = packages_from_report(binary_wheel_report)[0]

    with pytest.raises(ReportError):
        source_distribution_of(package, sdist_report)


def test_rejects_a_pass_that_lost_the_package(binary_wheel_report, sdist_report):
    sdist_report["install"] = []
    package = packages_from_report(binary_wheel_report)[0]

    with pytest.raises(ReportError):
        source_distribution_of(package, sdist_report)


def test_starts_no_pass_when_every_wheel_is_pure(report, source_passes):
    packages = packages_from_report(report)

    resolved = resolve_source_distributions(packages, source_passes)

    assert packages_of(source_passes) == []
    assert resolved[0].source.url.endswith("-py3-none-any.whl")


def test_starts_one_pass_for_a_binary_wheel(binary_wheel_report, source_passes):
    packages = packages_from_report(binary_wheel_report)

    resolved = resolve_source_distributions(packages, source_passes)

    assert packages_of(source_passes) == ["asyncpg"]
    assert resolved[0].source.url.endswith("asyncpg-0.30.0.tar.gz")


def test_substitutes_a_source_without_writing_to_the_package(
    binary_wheel_report, source_passes
):
    packages = packages_from_report(binary_wheel_report)

    resolved = resolve_source_distributions(packages, source_passes)

    assert packages[0].source.url.endswith(".whl")
    assert resolved[0] is not packages[0]


def test_refuses_a_write_to_a_package(report):
    package = packages_from_report(report)[0]

    with pytest.raises(FrozenInstanceError):
        package.source = None


def test_asks_for_one_package_per_pass(binary_wheel_report, report, source_passes):
    """
    The defect ADR-0005 removes: a pass naming several packages refuses
    a wheel to one that another one is built with.
    """
    packages = (
        packages_from_report(binary_wheel_report)
        + packages_from_report(maturin_report())
        + packages_from_report(report)
    )

    resolved = resolve_source_distributions(packages, source_passes)

    assert packages_of(source_passes) == ["asyncpg", "maturin"]
    assert [package.source.url.rsplit("/", 1)[-1] for package in resolved] == [
        "asyncpg-0.30.0.tar.gz",
        "maturin-1.14.1.tar.gz",
        "certifi-2026.1.1-py3-none-any.whl",
    ]


def test_reads_the_build_system_of_a_source(report, tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["hatchling"]\n'
    )
    report["install"][0]["download_info"] = {
        "url": f"file://{tmp_path}",
        "dir_info": {},
    }
    packages = packages_from_report(report)

    packages = read_build_systems(packages, ENVIRONMENT, sources())

    assert packages[0].setup_requires == ["hatchling"]
    assert packages[0].format == PYPROJECT


def test_reads_no_build_system_for_a_wheel(report):
    packages = packages_from_report(report)

    packages = read_build_systems(packages, ENVIRONMENT, sources())

    assert packages[0].setup_requires == []
    assert packages[0].format == WHEEL


def test_builds_a_source_without_a_build_system_the_legacy_way(report, tmp_path):
    (tmp_path / "setup.py").write_text("")
    report["install"][0]["download_info"] = {
        "url": f"file://{tmp_path}",
        "dir_info": {},
    }
    packages = packages_from_report(report)

    packages = read_build_systems(packages, ENVIRONMENT, sources())

    assert packages[0].setup_requires == []
    assert packages[0].format == SETUPTOOLS


def test_reads_the_build_system_of_a_git_checkout(git_report, tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools"]\n'
    )
    packages = packages_from_report(git_report)

    packages = read_build_systems(
        packages,
        ENVIRONMENT,
        sources(
            lambda url, revision, _hash: ("the-content-hash", revision, str(tmp_path))
        ),
    )

    assert packages[0].setup_requires == ["setuptools"]
    assert packages[0].format == PYPROJECT


def test_reads_the_license_and_the_classifier(trytond_report):
    expected = ["GPL-3", "GNU General Public License v3 or later (GPLv3+)"]

    packages = packages_from_report(trytond_report)

    assert package_named(packages, "trytond-account").licenses == expected


def test_reads_the_spdx_expression_of_a_package_that_declares_one(trytond_report):
    packages = packages_from_report(trytond_report)

    assert package_named(packages, "relatorio").licenses == ["GPL-3.0-or-later"]


def test_orders_the_licenses_with_the_spdx_expression_first(report):
    metadata = report["install"][0]["metadata"]
    metadata["license_expression"] = "Apache-2.0"
    metadata["license"] = "Apache 2.0"
    metadata["classifier"] = [
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
    ]

    assert packages_from_report(report)[0].licenses == [
        "Apache-2.0",
        "Apache 2.0",
        "Apache Software License",
    ]


def test_reads_no_license_from_metadata_that_declares_none(report):
    assert packages_from_report(report)[0].licenses == []


def test_drops_the_placeholder_setuptools_wrote_for_no_license(report):
    report["install"][0]["metadata"]["license"] = "UNKNOWN"

    assert packages_from_report(report)[0].licenses == []


def test_rejects_an_unknown_report_version(report):
    report["version"] = "2"

    with pytest.raises(ReportError):
        packages_from_report(report)


def test_rejects_a_source_without_a_sha256(report):
    del report["install"][0]["download_info"]["archive_info"]["hashes"]

    with pytest.raises(ReportError):
        packages_from_report(report)


def test_renders_a_git_source(git_report):
    prefetch_git = Mock(
        side_effect=lambda url, revision, _hash: (
            "the-content-hash",
            revision,
            "/store/repo",
        )
    )

    packages = resolve_sources(packages_from_report(git_report), sources(prefetch_git))

    assert packages[0].to_nix(NoLicenses()) == dedent("""\
        super.buildPythonPackage rec {
          pname = "six";
          version = "1.16.0";
          src = fetchgit {
            url = "https://github.com/benjaminp/six";
            rev = "65486e4383f9f411da95937451205d3c7b61b9e1";
            sha256 = "the-content-hash";
          };
          format = "setuptools";
          doCheck = false;
          buildInputs = [];
          nativeBuildInputs = [];
          propagatedBuildInputs = [];
        };""")


def test_rejects_a_mercurial_source(git_report):
    git_report["install"][0]["download_info"]["vcs_info"]["vcs"] = "hg"

    with pytest.raises(ReportError):
        packages_from_report(git_report)


def test_rejects_an_editable_requirement_from_a_requirements_file(report, tmpdir):
    report["install"][0]["download_info"] = {
        "url": f"file://{tmpdir}/src/certifi",
        "dir_info": {"editable": True},
    }

    with pytest.raises(ReportError):
        packages_from_report(report)


def test_renders_a_local_directory_without_a_hash(report, tmpdir):
    report["install"][0]["download_info"] = {
        "url": f"file://{tmpdir}",
        "dir_info": {},
    }

    package = packages_from_report(report)[0]

    assert package.source == LocalPath(url=f"file://{tmpdir}", path=str(tmpdir))


def test_reads_the_path_a_url_names(report):
    package = packages_from_report(report)[0]

    assert package.source.path == "/packages/certifi-2026.1.1-py3-none-any.whl"


def test_unquotes_the_path_of_a_file_url(report):
    report["install"][0]["download_info"] = {
        "url": "file:///tmp/a%20project",
        "dir_info": {},
    }

    package = packages_from_report(report)[0]

    assert package.source.path == "/tmp/a project"


def test_drops_the_fragment_from_the_url(report):
    report["install"][0]["download_info"]["url"] = (
        CERTIFI.wheel + "#sha256=" + "ab" * 32
    )

    package = packages_from_report(report)[0]

    assert package.source.url == CERTIFI.wheel


def test_drops_the_fragment_from_a_repository_url(git_report):
    url = git_report["install"][0]["download_info"]["url"]
    git_report["install"][0]["download_info"]["url"] = url + "#egg=six"

    package = packages_from_report(git_report)[0]

    assert package.source.url == url


def test_rejects_a_scheme_it_cannot_render(report):
    report["install"][0]["download_info"] = {"url": "ftp://index.example/certifi.tgz"}

    with pytest.raises(ReportError):
        packages_from_report(report)
