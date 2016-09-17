from configobj import ConfigObj
from functools import reduce
import io
import operator
import os
import pkg_resources
import validate


def flatten_validation_errors(errors):
    """Yields (path, error) pairs."""
    for section, value in errors.items():
        if value is True:
            continue
        elif value is False:
            yield section, 'value is missing'
        elif isinstance(value, dict):
            for path, errs in flatten_validation_errors(value):
                yield section + '.' + path, errs
        else:
            yield section, str(value)


class ValidationError(Exception):
    pass


class Config(object):
    """pip2nix configuration.

    This object handles merging and validation of CLI and .ini options."""

    def __init__(self):
        confspec = pkg_resources.resource_string(__name__, 'confspec.ini')
        self.config = ConfigObj(
            {}, configspec=io.StringIO(confspec.decode('utf-8')),
        )

    def __getitem__(self, key):
        return self.config[key]

    def get(self, key, default=None):
        try:
            self[key]
        except KeyError:
            return default

    def validate(self):
        """Check if configuration is OK, and raise a ValidationError if not."""
        validator = self._build_validator()
        errs = self.config.validate(validator, preserve_errors=True)
        if errs is not True:
            flat_errors = flatten_validation_errors(errs)
            err_msg = '\n'.join(
                path + ': ' + path_error
                for path, path_error in flat_errors)
            raise ValidationError(err_msg)

    def _build_validator(self):
        """Create a Validator with our custom rules included"""
        validator = validate.Validator()
        validator.functions['requirements_list'] = requirements_list_validator
        return validator

    def find_and_load(self):
        """Find a configuration file and load options from it."""
        base_path = os.getcwd()
        # Going up from CWD, find the first configuration file with [pip2nix*]
        while base_path != '/':
            path = os.path.join(base_path, 'pip2nix.ini')
            if os.path.exists(path):
                # Check if pip2nix sections exist in the file
                if self.load(path):
                    return
            base_path = os.path.dirname(base_path)

    def load(self, path):
        """Load configuration from path."""
        config = ConfigObj(path)
        if any(k == 'pip2nix' or k.startswith('pip2nix:') for k in config):
            # Only merge configuration files that actually support pip2nix
            self.merge_options(config.dict())
            return True
        return False

    def merge_options(self, options):
        # Expand sections with :
        for name, value in options.items():
            if ':' in name:
                opts = {}
                subopts = opts
                for elem in name.split(':'):
                    subopts[elem] = {}
                    last_subopts = subopts
                    subopts = subopts[elem]
                last_subopts[elem] = value
                self.merge_options(opts)
        self.config.merge(options)

    def merge_cli_options(self, cli_options):
        """Prepare the options before merging."""
        options = {}
        requirements = list(cli_options.get('specifiers', ()))
        requirements.extend(
            '-e ' + req for req in cli_options.get('editables', ()))
        requirements.extend(
            '-r ' + req for req in cli_options.get('requirements', ()))
        if requirements:
            options['requirements'] = requirements

        for key in ('index_url', 'extra_index_url', 'no_index', 'output',
                    'licenses'):
            try:
                value = cli_options[key]
                if value is not None:
                    options[key] = value
            except KeyError:
                pass

        self.merge_options({'pip2nix': options})

    def get_requirements(self):
        """Yields pairs of (type, requirement) for all requirements.

        type is one of None, '-e', '-r'.
        """
        for req in self['pip2nix']['requirements']:
            if req.startswith(('-e', '-r')):
                yield req[:2], req[2:].strip()
            else:
                yield None, req.strip()

    def get_indexes(self):
        c = self['pip2nix']
        if c['no_index']:
            return []
        return list(filter(
            None, [c['index_url']] + c['extra_index_url']
        ))

    def get_package_config(self, package):
        """Get configuration for given package pair."""
        return self.get_config('pip2nix', 'package', package)

    def get_config(self, *path):
        try:
            return reduce(operator.getitem, path, self)
        except (KeyError, IndexError):
            return None


def requirements_list_validator(value, **kwargs):
    value = validate.force_list(value, **kwargs)
    validate.is_string_list(value)
    # TODO: check the formatting here?
    return value
