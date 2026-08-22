"""
Dependency edges, rebuilt from what each package declares.

pip's installation report carries `metadata.requires_dist`, which is
what a package declares rather than the edges the resolver chose.
Attributing them means evaluating PEP 508 markers against the
environment pip resolved for and keeping only the names the resolution
actually contains.
"""

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from .errors import ReportError


def resolve_dependencies(entries, environment):
    """
    Map each entry's name to the packages it depends on.

    Names are canonical throughout, and the values are the
    `(name, version)` pairs `PythonPackage` renders.
    """
    packages = {
        canonicalize_name(entry["metadata"]["name"]): entry for entry in entries
    }
    extras = _active_extras(packages, environment)
    return {
        name: _dependencies_of(entry, packages, extras[name], environment)
        for name, entry in packages.items()
    }


def _dependencies_of(entry, packages, extras, environment):
    requirements = _active_requirements(entry, extras, environment)
    names = {canonicalize_name(requirement.name) for requirement in requirements}
    return sorted(
        (name, packages[name]["metadata"]["version"])
        for name in names
        if name in packages
    )


def _active_extras(packages, environment):
    """
    Grow the extras each package is used with until nothing changes.

    The report marks `requested_extras` only on the entries the user
    asked for, but an extra also reaches a package through a dependent
    asking for it -- `relatorio[fodt]` -- and what such an extra pulls
    in can ask for further extras in turn.
    """
    extras = {
        name: set(entry.get("requested_extras") or [])
        for name, entry in packages.items()
    }
    grew = True
    while grew:
        grew = False
        for name, entry in packages.items():
            for requirement in _active_requirements(entry, extras[name], environment):
                target = canonicalize_name(requirement.name)
                if target not in packages:
                    continue
                if not requirement.extras <= extras[target]:
                    extras[target] |= requirement.extras
                    grew = True
    return extras


def _active_requirements(entry, extras, environment):
    for declared in entry["metadata"].get("requires_dist") or []:
        requirement = _requirement_of(entry, declared)
        if _is_active(requirement.marker, extras, environment):
            yield requirement


def _requirement_of(entry, declared):
    try:
        return Requirement(declared)
    except InvalidRequirement as error:
        raise ReportError(
            f'Cannot read a requirement of "{entry["metadata"]["name"]}": {error}'
        )


def _is_active(marker, extras, environment):
    if marker is None or marker.evaluate(environment):
        return True
    return any(marker.evaluate(dict(environment, extra=extra)) for extra in extras)
