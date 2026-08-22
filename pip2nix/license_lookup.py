"""
Mapping a declared license name onto a `nixpkgs.lib.licenses` attribute, which
means asking nixpkgs what it knows.
"""

import json
import logging
from contextlib import suppress
from subprocess import CalledProcessError, TimeoutExpired, check_output

from .errors import ReportError


logger = logging.getLogger(__name__)

# Long enough that a registry which does answer is not cut off, short
# enough that one which does not costs a wait rather than an evening.
NIXPKGS_TIMEOUT_SECONDS = 30

# Mapping from license name in setup.py to attribute in nixpkgs.lib.licenses.
# TODO: Think about providing this from outside, maybe from a file.
case_sensitive_license_nix_map = {
    "Apache 2.0": "asl20",
    "Apache License, Version 2.0": "asl20",
    "Apache Software License": "asl20",
    "BSD license": "bsdOriginal",
    "BSD": "bsdOriginal",
    "GNU GPLv2 or any later version": "gpl2Plus",
    "GNU General Public License v2 or later (GPLv2+)": "gpl2Plus",
    "GNU General Public License v3 or later (GPLv3+)": "gpl3Plus",
    "GNU Lesser General Public License v2 or later (LGPLv2+)": "lgpl2Plus",
    "GPLv2 or later": "gpl2Plus",
    "GPLv2": "gpl2",
    "GPLv3": "gpl3",
    "LGPLv2.1 or later": "lgpl21Plus",
    "PSF License": "psfl",
    "PSF": "psfl",
    "Python Software Foundation License": "psfl",
    "Python style": "psfl",
    "Two-clause BSD license": "bsd2",
    "ZPL 2.1": "zpl21",
    "ZPL": "zpl21",
    "Zope Public License": "zpl21",
}
license_nix_map = {
    name.lower(): nix_attr for name, nix_attr in case_sensitive_license_nix_map.items()
}


class LicenseLookup:
    def __init__(self):
        self._nix_licenses = None

    def attribute_for(self, license_name):
        """
        The `nixpkgs.lib.licenses` attribute a license name maps to, if any.

        The names a package declares are free text, an SPDX identifier or a
        trove classifier, so the lookup goes through the hand-written map
        first and then through every value nixpkgs records for a license --
        `spdxId` among them, which is what makes SPDX identifiers resolve.
        """
        license_name = license_name.lower()

        attribute = license_nix_map.get(license_name)
        if attribute:
            return attribute

        for attribute, nix_license_data in self._known_to_nixpkgs().items():
            if license_name in nix_license_data.values():
                return attribute

        return None

    def _known_to_nixpkgs(self):
        if self._nix_licenses is None:
            self._nix_licenses = _ask_nixpkgs()
        return self._nix_licenses


def _ask_nixpkgs():
    nixpkgs = _resolve_nixpkgs()
    logger.info("Asking %s which licenses it knows.", nixpkgs)
    nix_licenses = _licenses_known_to(nixpkgs)
    _lowercase_names(nix_licenses)
    return nix_licenses


def _resolve_nixpkgs():
    return _nix_instantiate("<nixpkgs>").decode("utf-8").strip()


def _licenses_known_to(nixpkgs):
    # `lib.licenses` carries the SPDX operators `AND`, `OR`, `PLUS`
    # and `WITH` next to the licenses themselves, and `toJSON`
    # refuses to serialize a function.
    known = _nix_instantiate(
        f"with import {nixpkgs} {{ }}; builtins.toJSON "
        "(lib.filterAttrs (name: value: builtins.isAttrs value) "
        "lib.licenses)"
    )
    return json.loads(json.loads(known.decode("utf-8")))


def _lowercase_names(nix_licenses):
    for entry in nix_licenses.values():
        for key, value in entry.items():
            # A value without lower() is not a name to match against.
            with suppress(AttributeError):
                entry[key] = value.lower()


def _nix_instantiate(expression):
    try:
        return check_output(
            ["nix-instantiate", "--eval", "--expr", expression],
            timeout=NIXPKGS_TIMEOUT_SECONDS,
        )
    except TimeoutExpired:
        raise ReportError(
            "Cannot ask nixpkgs which licenses it knows: it did not answer "
            f"within {NIXPKGS_TIMEOUT_SECONDS}s. `--licenses` needs a "
            "`<nixpkgs>` on `NIX_PATH`; without one the flake registry is "
            "fetched from instead."
        )
    except (OSError, CalledProcessError) as error:
        raise ReportError(
            f"Cannot ask nixpkgs which licenses it knows: {error}. "
            "`--licenses` needs a `<nixpkgs>` that resolves."
        )
