import os
from dataclasses import dataclass, field

from .source import FetchGit, FetchUrl, LocalPath, Source


# The `buildPythonPackage` builders pip2nix generates.
WHEEL = "wheel"
SETUPTOOLS = "setuptools"
PYPROJECT = "pyproject"

# Written out rather than joined, so the source shows the shape it
# emits. Both are `str.format` templates, hence the doubled braces.
_PACKAGE_TEMPLATE = """\
super.buildPythonPackage rec {{
  {args}
}};"""

_META_TEMPLATE = """\
meta = {{
  {meta_args}
}};"""

# Rendered in this order; every other argument follows them sorted.
_LEADING_ARGUMENTS = ("pname", "version", "src", "format", "doCheck")


def indent(amount, string):
    lines = string.splitlines()
    if len(lines) == 0:
        return ""
    elif len(lines) == 1:
        return lines[0]
    else:
        return lines[0] + "\n" + "\n".join(" " * amount + line for line in lines[1:])


@dataclass(frozen=True)
class PythonPackage:
    """
    A package as the arguments ``buildPythonPackage`` takes, rather than
    as facts about a Python package.

    :param dependencies: list of (name, version) pairs.
    :param setup_requires: names of the packages needed to build it.
    :param licenses: license names as declared, most authoritative
        spelling first.
    :param format: the `buildPythonPackage` builder, decided by the
        adapter from what the source declares.
    """

    name: str
    version: str
    dependencies: list[tuple[str, str]]
    source: Source
    setup_requires: list[str] = field(default_factory=list)
    licenses: list[str] = field(default_factory=list)
    format: str = SETUPTOOLS

    def to_nix(self, nix_licenses):
        return _PACKAGE_TEMPLATE.format(args=indent(2, self._arguments(nix_licenses)))

    def _arguments(self, nix_licenses):
        arguments = self._build_arguments()
        trailing = sorted(set(arguments) - set(_LEADING_ARGUMENTS))
        rendered = [
            f"{name} = {arguments[name]};" for name in (*_LEADING_ARGUMENTS, *trailing)
        ]

        meta = self._meta(nix_licenses)
        if meta:
            rendered.append(meta)

        return "\n".join(rendered)

    def _build_arguments(self):
        return dict(
            pname=f'"{self.name}"',
            version=f'"{self.version}"',
            format=f'"{self.format}"',
            doCheck="false",
            src=source_to_nix(self.source),
            buildInputs=_nix_list([]),
            nativeBuildInputs=_nix_list(self._native_build_inputs()),
            propagatedBuildInputs=_nix_list(self._propagated_build_inputs()),
        )

    def _propagated_build_inputs(self):
        return [f'self."{name}"' for name, _version in self.dependencies]

    def _native_build_inputs(self):
        unzip = ['pkgs."unzip"'] if self.source.url.endswith("zip") else []
        return unzip + [f'self."{name}"' for name in self.setup_requires]

    def _meta(self, nix_licenses):
        arguments = self._meta_args(nix_licenses)
        if not arguments:
            return ""
        rendered = "".join(
            f"{name} = {value};\n" for name, value in sorted(arguments.items())
        )
        return _META_TEMPLATE.format(meta_args=indent(2, rendered))

    def _meta_args(self, nix_licenses):
        license_nix = nix_licenses.to_nix(self.licenses, self.name)
        return {"license": license_nix} if license_nix else {}


def _nix_list(entries):
    if not entries:
        return "[]"
    return "[\n  " + "\n  ".join(entries) + "\n]"


def source_to_nix(source):
    match source:
        case FetchGit():
            return _fetchgit_to_nix(source)
        case LocalPath():
            return "./" + os.path.relpath(source.path)
        case FetchUrl():
            return _fetchurl_to_nix(source)
        case _:
            raise TypeError(
                f"Cannot render {source!r}. The adapter resolves a source into "
                "what fetches it before rendering starts."
            )


def _fetchgit_to_nix(source):
    return "\n".join(
        (
            "fetchgit {",
            f'  url = "{source.url}";',
            f'  rev = "{source.rev}";',
            f'  sha256 = "{source.sha256}";',
            "}",
        )
    )


def _fetchurl_to_nix(source):
    return "\n".join(
        (
            "fetchurl {",
            f'  url = "{source.url}";',
            f'  sha256 = "{source.sha256}";',
            "}",
        )
    )
