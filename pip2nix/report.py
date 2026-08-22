"""
Translation of pip's installation report into packages and sources.

The report is the documented, versioned JSON description of what pip would
install. This module reads it and completes what it does not carry -- a
build backend, a source resolved to what fetches it -- through the
collaborators it is handed. The run that produced the report belongs to
`resolver.py`, and nothing here knows how pip is invoked.
"""

from dataclasses import replace
from urllib.parse import unquote, urlsplit

from packaging.utils import canonicalize_name

from .build_system import read_build_system
from .dependencies import resolve_dependencies
from .errors import ReportError
from .models.package import PYPROJECT, SETUPTOOLS, WHEEL, PythonPackage
from .models.source import Archive, FileSource, LocalPath, Repository


REPORT_VERSION = "1"

REMOTE_SCHEMES = ("http", "https")

LICENSE_CLASSIFIER = "License ::"


def resolve_packages(resolver, sources, only_direct=False, excluded=()):
    resolver.check_version()
    report = resolver.resolve()
    packages = packages_from_report(report, only_direct=only_direct, excluded=excluded)
    packages = resolve_source_distributions(packages, resolver)
    packages = read_build_systems(packages, report["environment"], sources)
    return resolve_sources(packages, sources)


def packages_from_report(report, only_direct=False, excluded=()):
    entries = _without_excluded(_entries_of(report), excluded)
    dependencies = resolve_dependencies(entries, report["environment"])
    if only_direct:
        entries = [entry for entry in entries if entry["requested"]]
    return [_package_from_entry(entry, dependencies) for entry in entries]


def resolve_source_distributions(packages, resolver):
    return [_with_source_distribution(package, resolver) for package in packages]


def _with_source_distribution(package, resolver):
    if not needs_source_distribution(package.source):
        return package
    report = resolver.resolve_source(package)
    return replace(package, source=source_distribution_of(package, report))


def needs_source_distribution(source):
    """
    Whether Nix can build from the file pip resolved to.

    A wheel built for a platform links against libraries at paths that do not
    exist in the store, so ADR-0003 replaces it with the project's sdist. A
    `-any` wheel carries the same modules its sdist does and is left alone.
    """
    if not isinstance(source, FileSource):
        return False
    return source.path.endswith(".egg") or (
        _is_wheel(source) and not source.path.endswith("-any.whl")
    )


def _is_wheel(source):
    return isinstance(source, FileSource) and source.path.endswith(".whl")


def source_distribution_of(package, report):
    entries = {_name_of(entry): entry for entry in _entries_of(report)}
    try:
        entry = entries[package.name]
    except KeyError:
        raise ReportError(
            f'Resolving "{package.name}" from its source distribution did not produce '
            "it at all."
        )
    if entry["metadata"]["version"] != package.version:
        raise ReportError(
            'Resolving "{name}" from its source distribution produced '
            "version {sdist} where the wheel resolved to {wheel}. Refusing "
            "to pin a source the rendered metadata does not describe.".format(
                name=package.name,
                sdist=entry["metadata"]["version"],
                wheel=package.version,
            )
        )
    return _source_from_download_info(entry["download_info"])


def read_build_systems(packages, environment, sources):
    """
    Give every package the builder it declares and the backend it needs.

    The report carries core metadata, which has no build-system field, so the
    source itself is the only place this can come from. Deciding it here rather
    than in the renderer is what keeps the renderer from having to read
    sources.
    """
    return [_with_build_system(package, environment, sources) for package in packages]


def _with_build_system(package, environment, sources):
    if _is_wheel(package.source):
        return replace(package, format=WHEEL)
    path = sources.local_path(package.source)
    build_system = read_build_system(path, environment)
    return replace(
        package,
        setup_requires=build_system.requires,
        format=PYPROJECT if build_system.declared else SETUPTOOLS,
    )


def resolve_sources(packages, sources):
    """
    Give every package the source the generated file fetches it with.
    """
    return [
        replace(package, source=sources.resolved(package.source))
        for package in packages
    ]


def _entries_of(report):
    version = report.get("version")
    if version != REPORT_VERSION:
        raise ReportError(
            f'Cannot read an installation report of version "{version}", '
            f'pip2nix understands version "{REPORT_VERSION}".'
        )
    return report["install"]


def _without_excluded(entries, excluded):
    """
    Drop the packages a consumer does not want generated.

    Removing them before dependencies are attributed also removes the
    edges naming them, so an excluded package is absent from the file
    entirely. `only_direct` filters after attribution instead, so that
    a package it emits keeps propagating what it needs.
    """
    excluded_names = {canonicalize_name(name) for name in excluded}
    return [entry for entry in entries if _name_of(entry) not in excluded_names]


def _name_of(entry):
    return canonicalize_name(entry["metadata"]["name"])


def _package_from_entry(entry, dependencies):
    metadata = entry["metadata"]
    name = _name_of(entry)
    return PythonPackage(
        name=name,
        version=metadata["version"],
        dependencies=dependencies[name],
        source=_source_from_download_info(entry["download_info"]),
        licenses=_licenses_from_metadata(metadata),
    )


def _licenses_from_metadata(metadata):
    """
    The licenses a package declares, most authoritative spelling first.

    PEP 639 replaced both the free text `License` field and the
    `License ::` classifiers with an SPDX expression, and a package can
    carry any combination of the three.
    """
    candidates = [
        metadata[field]
        for field in ("license_expression", "license")
        if metadata.get(field)
    ]
    candidates.extend(
        classifier.split("::")[-1].strip()
        for classifier in metadata.get("classifier", ())
        if classifier.startswith(LICENSE_CLASSIFIER)
    )
    # setuptools used to write the placeholder out as a license itself.
    return [candidate for candidate in candidates if candidate != "UNKNOWN"]


def _source_from_download_info(download_info):
    url = download_info["url"].split("#", 1)[0]
    if "vcs_info" in download_info:
        return _repository_source(url, download_info["vcs_info"])
    if download_info.get("dir_info", {}).get("editable"):
        raise ReportError(
            f'Cannot generate a source for "{url}": the report describes an '
            "editable requirement as the local directory it would be "
            "checked out into, which loses the url and the revision it "
            "comes from."
        )

    return _file_source(url, download_info)


def _repository_source(url, vcs_info):
    vcs = vcs_info["vcs"]
    if vcs != "git":
        raise ReportError(
            f'Cannot generate a source for "{url}": pip2nix renders git '
            f"repositories, this one is {vcs}."
        )
    return Repository(url=url, commit_id=vcs_info["commit_id"])


def _file_source(url, download_info):
    parts = urlsplit(url)
    path = unquote(parts.path)
    if parts.scheme in REMOTE_SCHEMES:
        return Archive(url=url, path=path, sha256_hex=_sha256_of(download_info))
    if parts.scheme == "file":
        return LocalPath(url=url, path=path)
    raise ReportError(
        f'Cannot generate a source for "{url}": pip2nix renders http, https '
        f'and file sources, this one is "{parts.scheme}".'
    )


def _sha256_of(download_info):
    hashes = download_info.get("archive_info", {}).get("hashes", {})
    try:
        return hashes["sha256"]
    except KeyError:
        raise ReportError(
            'The index published no sha256 for "{}". Refusing to generate '
            "a source without a hash to pin it.".format(download_info["url"])
        )
