"""
The example urls the unit tests build sources from.

They name hosts that resolve nowhere, so a test reaching the network
fails rather than quietly succeeding. Grouping the certifi three keeps
the shapes of one release together: an index serves the same version as
a wheel, an sdist and a zip, and which one a source carries is what
several tests are about.
"""

from types import SimpleNamespace


CERTIFI = SimpleNamespace(
    wheel="https://index.example/packages/certifi-2026.1.1-py3-none-any.whl",
    sdist="https://index.example/packages/certifi-2026.1.1.tar.gz",
    zip="https://index.example/packages/certifi-2026.1.1.zip",
)

REPOSITORY = "https://git.example/repo"
