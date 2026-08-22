"""
The build backend a source declares, read from its `pyproject.toml`.

pip's installation report carries core metadata, which has no build-system
field, so this is the one thing about a package the report cannot answer and
the source itself has to. Only sources need it: a wheel is already built, which
is why ADR-0003 leaves the ones Nix can use alone.
"""

import os
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass, field

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


PYPROJECT = "pyproject.toml"


@dataclass(frozen=True)
class BuildSystem:
    """
    A table naming no requirements still declares a backend, so `declared` is a
    field of its own rather than `bool(requires)`.
    """

    requires: list[str] = field(default_factory=list)
    declared: bool = False


def read_build_system(path, environment):
    """
    The `[build-system]` table of the source at `path`, a directory or an
    archive.

    A `pyproject.toml` holding only `[tool.*]` configuration
    declares nothing, as does a bare `setup.py` project.
    """
    table = _read_pyproject(path).get("build-system")
    if table is None:
        return BuildSystem()
    return BuildSystem(
        requires=_requirement_names(table.get("requires") or [], environment),
        declared=True,
    )


def _read_pyproject(path):
    if os.path.isdir(path):
        return _load(os.path.join(path, PYPROJECT))
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            return _load_member(archive.namelist(), archive.read)
    if tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            return _load_member(
                archive.getnames(), lambda name: archive.extractfile(name).read()
            )
    return {}


def _load(path):
    if not os.path.isfile(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_member(names, read):
    member = _root_pyproject(names)
    return tomllib.loads(read(member).decode("utf-8")) if member else {}


def _root_pyproject(names):
    """
    The `pyproject.toml` an archive keeps in its single root directory, as in
    `asyncpg-0.30.0/pyproject.toml`.
    """
    for name in names:
        parts = [part for part in name.split("/") if part not in ("", ".")]
        if len(parts) == 2 and parts[1] == PYPROJECT:
            return name
    return None


def _requirement_names(requires, environment):
    names = []
    for declared in requires:
        requirement = Requirement(declared)
        if requirement.marker and not requirement.marker.evaluate(environment):
            continue
        name = canonicalize_name(requirement.name)
        if name not in names:
            names.append(name)
    return names
