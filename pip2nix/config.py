import io
import operator
import os
from collections.abc import Iterator
from functools import reduce

import validate
from configobj import ConfigObj

from . import resources


# The options `generate` accepts on the command line and in a
# configuration file alike. Both spellings reach the same key, so a
# command-line default that is not "absent" overwrites what the file
# said -- which is why each of these has to arrive as None when it was
# not given.
MERGED_CLI_OPTIONS = (
    "index_url",
    "extra_index_url",
    "no_index",
    "output",
    "licenses",
    "only_direct",
)


def flatten_validation_errors(errors):
    """
    Yields (path, error) pairs.
    """
    for section, value in errors.items():
        if value is True:
            continue
        elif value is False:
            yield section, "value is missing"
        elif isinstance(value, dict):
            for path, errs in flatten_validation_errors(value):
                yield section + "." + path, errs
        else:
            yield section, str(value)


class ValidationError(Exception):
    pass


class Config:
    """
    Pip2nix configuration.

    This object handles merging and validation of CLI and .ini options.
    """

    def __init__(self):
        self.config = ConfigObj(
            {},
            configspec=io.StringIO(resources.read_text("confspec.ini")),
        )

    def __getitem__(self, key):
        return self.config[key]

    def validate(self):
        """
        Check if configuration is OK, and raise a ValidationError if not.
        """
        self._refuse_package_configuration()
        validator = self._build_validator()
        errs = self.config.validate(validator, preserve_errors=True)
        if errs is not True:
            flat_errors = flatten_validation_errors(errs)
            err_msg = "\n".join(
                path + ": " + path_error for path, path_error in flat_errors
            )
            raise ValidationError(err_msg)

    def _refuse_package_configuration(self):
        """
        Reject a section pip2nix parses but never applied.

        ConfigObj ignores a section its configspec does not declare, so
        dropping it from `confspec.ini` would let it pass in silence --
        which is what kept it unnoticed while nothing read it.
        """
        packages = self.get_config("pip2nix", "package")
        if not packages:
            return
        sections = ", ".join(f"[pip2nix:package:{name}]" for name in sorted(packages))
        raise ValidationError(
            "pip2nix does not apply per-package configuration, remove "
            f"it: {sections}. Attributes for a generated package belong "
            "in the overrides layer beside the generated file, which is "
            "where they take effect."
        )

    def _build_validator(self):
        """
        Create a Validator with our custom rules included.
        """
        validator = validate.Validator()
        validator.functions["strings"] = strings_validator
        return validator

    def find_and_load(self):
        """
        Find a configuration file and load options from it.
        """
        base_path = os.getcwd()
        # Going up from CWD, find the first configuration file with [pip2nix*]
        while base_path != "/":
            path = os.path.join(base_path, "pip2nix.ini")
            if os.path.exists(path) and self.load(path):
                return
            base_path = os.path.dirname(base_path)

    def load(self, path):
        """
        Load configuration from path.
        """
        config = ConfigObj(path)
        if any(k == "pip2nix" or k.startswith("pip2nix:") for k in config):
            # Only merge configuration files that actually support pip2nix
            self.merge_options(config.dict())
            return True
        return False

    def merge_options(self, options):
        # Expand sections with :
        for name, value in options.items():
            if ":" in name:
                opts = {}
                subopts = opts
                for elem in name.split(":"):
                    subopts[elem] = {}
                    last_subopts = subopts
                    subopts = subopts[elem]
                last_subopts[elem] = value
                self.merge_options(opts)
        self.config.merge(options)

    def merge_cli_options(self, cli_options):
        """
        Prepare the options before merging.
        """
        options = {}
        requirements = list(cli_options.get("specifiers", ()))
        requirements.extend("-e " + req for req in cli_options.get("editables", ()))
        requirements.extend("-r " + req for req in cli_options.get("requirements", ()))
        if requirements:
            options["requirements"] = requirements

        constraints = cli_options.get("constraints", ())
        if constraints:
            options["constraints"] = constraints

        for key in MERGED_CLI_OPTIONS:
            value = cli_options.get(key)
            if _was_given(value):
                options[key] = value

        self.merge_options({"pip2nix": options})

    def get_requirements(self) -> Iterator[tuple[str | None, str]]:
        for req in self["pip2nix"]["requirements"]:
            if req.startswith(("-e", "-r")):
                yield req[:2], req[2:].strip()
            else:
                yield None, req.strip()

    @property
    def constraints(self) -> list[str]:
        return self["pip2nix"]["constraints"]

    @property
    def output(self) -> str:
        return self["pip2nix"]["output"]

    @property
    def only_direct(self) -> bool:
        return self["pip2nix"]["only_direct"]

    @property
    def licenses(self) -> bool:
        return self["pip2nix"]["licenses"]

    @property
    def excluded_packages(self) -> list[str]:
        return self["pip2nix"]["excluded_packages"]

    @property
    def indexes(self) -> list[str]:
        c = self["pip2nix"]
        if c["no_index"]:
            return []
        return list(filter(None, [c["index_url"]] + c["extra_index_url"]))

    def get_config(self, *path):
        try:
            return reduce(operator.getitem, path, self)
        except (KeyError, IndexError):
            return None


def _was_given(value):
    """
    Whether the command line carried the option at all.

    click reports an absent option as None, except a `multiple` one,
    which arrives as an empty tuple. Neither is an answer, so neither
    may overwrite what a configuration file said.
    """
    return value is not None and value != ()


def strings_validator(value, **kwargs):
    """
    A list of strings, written as one value or as several.

    ConfigObj's own `string_list` refuses a single value unless it
    carries a trailing comma, and reports that as a type error which
    says nothing about commas.
    """
    return validate.is_string_list(validate.force_list(value, **kwargs))
