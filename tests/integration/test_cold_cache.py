"""
The guard for ADR-0005, which needs a real index to say anything.

pip caches a wheel it built, so the backend of a package resolved from source
is compiled once and read from the cache forever after. That is why the defect
this checks for was invisible on the machine that had already paid for it, and
why every run here gets a cache of its own.
"""

import os
import sys

import pytest

from pip2nix.config import Config
from pip2nix.models.source import Sources
from pip2nix.prefetch import prefetch_git, prefetch_url_path
from pip2nix.report import resolve_packages
from pip2nix.resolver import Resolver


# Resolving a source distribution reads its build system out of the
# store, so this reaches `nix-prefetch-url` as well as the index.
pytestmark = [pytest.mark.nix, pytest.mark.network]

# pydantic-core is built with maturin and asks for no wheel Nix can use,
# so it is resolved from source; maturin is requested beside it, which
# makes it a package pip2nix renders and a backend pip needs at once.
REQUIREMENTS = ["pydantic-core==2.41.5", "maturin"]


@pytest.fixture
def cold_cache(tmp_path, mocker):
    cache = tmp_path / "pip-cache"
    mocker.patch.dict(os.environ, {"PIP_CACHE_DIR": str(cache)})
    return cache


def test_resolves_from_source_without_building_the_backend(cold_cache):
    config = make_config(REQUIREMENTS)

    packages = resolve_packages(
        Resolver(os.environ.get("PIP2NIX_PYTHON_EXECUTABLE", sys.executable), config),
        Sources(prefetch_git, prefetch_url_path, {}),
        only_direct=config.only_direct,
    )

    # An empty `wheels` directory is also what a cache pip never opened
    # returns, so the guard first needs proof the fixture reached pip.
    assert cache_entries(cold_cache) != []
    assert built_wheels(cold_cache) == []
    assert sorted(source_file(package) for package in packages) == [
        "maturin-1.14.1.tar.gz",
        "pydantic_core-2.41.5.tar.gz",
    ]


def make_config(requirements):
    config = Config()
    config.merge_options(
        {
            "pip2nix": {
                "requirements": requirements,
                "only_direct": True,
            }
        }
    )
    config.validate()
    return config


def built_wheels(cache):
    return files_under(cache / "wheels")


def cache_entries(cache):
    return files_under(cache)


def files_under(directory):
    return [name for _root, _dirs, names in os.walk(str(directory)) for name in names]


def source_file(package):
    return package.source.url.rsplit("/", 1)[-1]
