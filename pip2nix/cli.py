import logging
import os
import sys

import click
import jinja2
from packaging.utils import canonicalize_name

import pip2nix

from . import resources
from .config import Config, ValidationError
from .errors import ReportError
from .license_lookup import LicenseLookup
from .models.license import NixLicenses, NoLicenses
from .models.source import Sources
from .output import read_repository_hashes, write_output
from .prefetch import prefetch_git, prefetch_url_path
from .report import resolve_packages
from .resolver import Resolver


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--output", metavar="<path>", help="Write the generated nix to <path>.")
@click.option(
    "--only-direct", is_flag=True, default=None, help="Only render direct dependencies."
)
@click.option(
    "--index-url", "-i", metavar="<url>", help="Base URL of Python Package Index."
)
@click.option(
    "--extra-index-url", multiple=True, metavar="<url>", help="Extra index URLs to use."
)
@click.option("--no-index/--index", default=None, help="Ignore indexes.")
@click.option(
    "--configuration", metavar="<path>", help="Read pip2nix configuration from <path>."
)
@click.option(
    "--editable",
    "-e",
    multiple=True,
    type=click.Path(),
    metavar="<spec>",
    help="Add an editable requirement, which pip2nix refuses to render.",
)
@click.option(
    "--requirement",
    "-r",
    multiple=True,
    type=click.Path(),
    metavar="<file>",
    help="Load specifiers from a requirements file.",
)
@click.option(
    "--constraint",
    "-c",
    multiple=True,
    type=click.Path(),
    metavar="<file>",
    help="Constrain versions based on the constraints file.",
)
@click.option(
    "--licenses/--no-licenses",
    default=None,
    help="Extract license information as well, off by default.",
)
@click.argument("specifiers", nargs=-1)
def generate(specifiers, **kwargs):
    """
    Generate a .nix file with specified packages.
    """
    kwargs["specifiers"] = specifiers
    kwargs["editables"] = kwargs.pop("editable", ())
    kwargs["requirements"] = kwargs.pop("requirement", None)
    kwargs["constraints"] = kwargs.pop("constraint", None)

    config = Config()
    if kwargs["configuration"]:
        config.load(kwargs["configuration"])
    else:
        config.find_and_load()
    config.merge_cli_options(kwargs)
    validate_configuration(config)

    python_executable = os.environ.get("PIP2NIX_PYTHON_EXECUTABLE") or sys.executable
    output = config.output
    sources = Sources(prefetch_git, prefetch_url_path, read_repository_hashes(output))
    nix_licenses = (
        NixLicenses(LicenseLookup().attribute_for) if config.licenses else NoLicenses()
    )
    # Resolving and rendering both reach the network and the nix store, so
    # both fail in ways the user can act on. Reporting them together is what
    # keeps a failed run from ending in a traceback.
    try:
        packages = resolve_packages(
            Resolver(python_executable, config),
            sources,
            only_direct=config.only_direct,
            excluded=config.excluded_packages,
        )
        write_output(output, packages, nix_licenses)
    except ReportError as error:
        raise click.ClickException(str(error))


@cli.command()
@click.option(
    "--configuration", metavar="<path>", help="Read pip2nix configuration from <path>."
)
@click.option(
    "--output",
    metavar="<path>",
    default="default.nix",
    help="Write the generated file to <path>.",
)
@click.option(
    "--overrides-output",
    metavar="<path>",
    default="python-packages-overrides.nix",
    help="Write the generated overrides file to <path>.",
)
@click.option(
    "--package",
    metavar="<package>",
    required=True,
    help="Name of the package the scaffold is for.",
)
def scaffold(output, overrides_output, **kwargs):
    config = Config()
    if kwargs["configuration"]:
        config.load(kwargs["configuration"])
    else:
        config.find_and_load()
    config.merge_cli_options(kwargs)
    # TODO: Config enforces requirements to be specified, find a nicer
    # way to let Config know that we don't need requirements here.
    config.merge_options({"pip2nix": {"requirements": []}})
    validate_configuration(config)

    write_template(
        "default.nix.j2", output, package_name=canonicalize_name(kwargs["package"])
    )
    write_template("python-packages-overrides.nix.j2", overrides_output)


def validate_configuration(config):
    try:
        config.validate()
    except ValidationError as error:
        raise click.ClickException(str(error))


def write_template(template_name, output, **context):
    template = jinja2.Template(resources.read_text(template_name))
    rendered = template.render(pip2nix_version=pip2nix.__version__, **context)
    with open(output, "w") as f:
        f.write(rendered)
