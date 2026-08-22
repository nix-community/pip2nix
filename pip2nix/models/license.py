"""
Rendering what a package declares as the `meta.license` nixpkgs takes.
"""

import logging
import re

from packaging.licenses import (
    InvalidLicenseExpression,
    canonicalize_license_expression,
)


logger = logging.getLogger(__name__)


class NixLicenses:
    """
    What nixpkgs knows about licenses, as the renderer needs it.
    """

    def __init__(self, attribute_of):
        self._attribute_of = attribute_of

    def to_nix(self, licenses, package_name):
        """
        The `meta.license` value, or None when nothing is declared.

        Only the spellings nixpkgs knows are rendered, an SPDX expression
        as every attribute it names. When nixpkgs knows none of them the
        most authoritative spelling is kept as a full name, which is the
        shape `nixpkgs.lib.licenses` entries have anyway.
        """
        attributes = []
        for license_name in licenses:
            for attribute in self._attributes_of(license_name):
                if attribute not in attributes:
                    attributes.append(attribute)

        if attributes:
            rendered = [_attribute_to_nix(attribute) for attribute in attributes]
        elif licenses:
            self._warn_kept_as_full_name(licenses[0], package_name)
            rendered = [_full_name_to_nix(licenses[0])]
        else:
            return None

        return "[ {licenses} ]".format(licenses=" ".join(rendered))

    def _attributes_of(self, declared):
        """
        Every attribute a declared license resolves to, or none at all.

        An SPDX expression names distinct licenses, so one nixpkgs does
        not know makes the whole expression unusable: rendering the rest
        would state something narrower than the package declares.
        """
        attributes = [
            self._attribute_of(member) for member in self._members_of(declared)
        ]
        return attributes if all(attributes) else []

    def _members_of(self, declared):
        """
        The licenses a declared string names: itself, unless it is an
        expression naming several.
        """
        if self._attribute_of(declared):
            return [declared]
        return license_expression_members(declared) or [declared]

    def _warn_kept_as_full_name(self, declared, package_name):
        unresolved = [
            member
            for member in self._members_of(declared)
            if not self._attribute_of(member)
        ]
        logger.warning(
            'Keeping the license of "%s" as a full name: nixpkgs has no attribute for %s.',
            package_name,
            ", ".join(unresolved),
        )


class NoLicenses:
    def to_nix(self, licenses, package_name):
        return None


_HAS_NO_LIST_FORM = re.compile(r"[()]|\sWITH\s")
_OPERATOR = re.compile(r"\s(?:AND|OR)\s")


def license_expression_members(declared):
    """
    The licenses an SPDX expression names, or None when it names none.

    `WITH` and parentheses have no list form in `meta.license`, which
    does not distinguish `AND` from `OR` either, so an expression
    carrying one of them is left to the caller rather than guessed at.
    """
    try:
        expression = canonicalize_license_expression(declared)
    except InvalidLicenseExpression:
        return None

    if _HAS_NO_LIST_FORM.search(expression):
        return None

    return _OPERATOR.split(expression)


def _attribute_to_nix(attribute):
    return f"pkgs.lib.licenses.{attribute}"


def _full_name_to_nix(license_name):
    return f'{{ fullName = "{_escape_nix_string(license_name)}"; }}'


def _escape_nix_string(value):
    """
    A string the index declared, made safe to place inside a Nix literal.

    Nothing upstream of this constrains what a package declares, and an
    unescaped quote ends the attribute while `${` starts an
    interpolation.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return escaped.replace("${", "\\${")
