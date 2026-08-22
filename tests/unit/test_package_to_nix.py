from textwrap import dedent

import pytest

from pip2nix.models.license import NoLicenses
from pip2nix.models.package import (
    PYPROJECT,
    SETUPTOOLS,
    WHEEL,
    PythonPackage,
)
from pip2nix.models.source import FetchUrl

from ..doubles import nix_licenses, nix_licenses_that_must_not_be_asked
from .digests import SHA256_BASE32
from .urls import CERTIFI


def make_package(
    url, dependencies=(), licenses=(), setup_requires=(), format=SETUPTOOLS
):
    return PythonPackage(
        name="certifi",
        version="2026.1.1",
        dependencies=list(dependencies),
        source=archive(url),
        licenses=list(licenses),
        setup_requires=list(setup_requires),
        format=format,
    )


def archive(url):
    return FetchUrl(url=url, sha256=SHA256_BASE32)


@pytest.fixture
def renders_a_known_license():
    """
    Renders licenses, standing in for the lookup that needs nix.
    """
    return nix_licenses({"GPL-3.0-or-later": "gpl3Plus"})


def test_renders_a_wheel():
    package = make_package(CERTIFI.wheel, format=WHEEL)

    assert package.to_nix(NoLicenses()) == dedent("""\
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


def test_renders_every_argument_in_order(renders_a_known_license):
    package = make_package(
        CERTIFI.zip,
        dependencies=[("idna", "3.18"), ("urllib3", "2.7.0")],
        licenses=["GPL-3.0-or-later"],
        setup_requires=["setuptools", "cython"],
    )

    assert package.to_nix(renders_a_known_license) == dedent("""\
        super.buildPythonPackage rec {
          pname = "certifi";
          version = "2026.1.1";
          src = fetchurl {
            url = "https://index.example/packages/certifi-2026.1.1.zip";
            sha256 = "04mmsvw5c0ps2gh6hqwkcs5gyyvmfpr32zvxmv3w68a2mn5kwm39";
          };
          format = "setuptools";
          doCheck = false;
          buildInputs = [];
          nativeBuildInputs = [
            pkgs."unzip"
            self."setuptools"
            self."cython"
          ];
          propagatedBuildInputs = [
            self."idna"
            self."urllib3"
          ];
          meta = {
            license = [ pkgs.lib.licenses.gpl3Plus ];
          };
        };""")


@pytest.mark.parametrize("format", [SETUPTOOLS, PYPROJECT, WHEEL])
def test_renders_the_format_it_was_given(format):
    package = make_package(CERTIFI.sdist, format=format)

    assert f'format = "{format}";' in package.to_nix(NoLicenses())


def test_renders_dependencies_as_propagated_build_inputs():
    expected = dedent("""\
        propagatedBuildInputs = [
            self."idna"
            self."urllib3"
          ];""")

    package = make_package(
        CERTIFI.wheel, dependencies=[("idna", "3.18"), ("urllib3", "2.7.0")]
    )

    assert expected in package.to_nix(NoLicenses())


def test_renders_unzip_for_a_zip_source():
    assert 'nativeBuildInputs = [\n    pkgs."unzip"\n  ];' in make_package(
        CERTIFI.zip
    ).to_nix(NoLicenses())


def test_renders_build_requirements_as_native_build_inputs():
    expected = dedent("""\
        nativeBuildInputs = [
            self."setuptools"
            self."cython"
          ];""")

    package = make_package(CERTIFI.sdist, setup_requires=["setuptools", "cython"])

    assert expected in package.to_nix(NoLicenses())


def test_renders_unzip_next_to_the_build_requirements():
    expected = dedent("""\
        nativeBuildInputs = [
            pkgs."unzip"
            self."setuptools"
          ];""")

    package = make_package(CERTIFI.zip, setup_requires=["setuptools"])

    assert expected in package.to_nix(NoLicenses())


def test_renders_the_declared_license_into_meta(renders_a_known_license):
    expected = dedent("""\
        meta = {
            license = [ pkgs.lib.licenses.gpl3Plus ];
          };""")

    package = make_package(CERTIFI.wheel, licenses=["GPL-3.0-or-later"])

    assert expected in package.to_nix(renders_a_known_license)


def test_renders_no_meta_when_licenses_are_not_rendered():
    package = make_package(CERTIFI.wheel, licenses=["GPLv3"])

    assert "meta" not in package.to_nix(NoLicenses())


def test_renders_no_meta_for_a_package_that_declares_no_license():
    assert "meta" not in make_package(CERTIFI.wheel).to_nix(
        nix_licenses_that_must_not_be_asked()
    )
