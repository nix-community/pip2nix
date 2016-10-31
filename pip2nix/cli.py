import click
import pkg_resources
from .config import Config


@click.group()
def cli():
    pass


@cli.command()
@click.option('--build', '-b', type=click.Path(), metavar='<dir>',
              help="Directory to unpack packages and build in.")
@click.option('--download', '-d', type=click.Path(), metavar='<dir>',
              help="Directory to download packages to.")
# TODO:
#@click.option('--pre/--no-pre',
#              help="Also look for pre-release and unstable versions.")
@click.option('--output', metavar='<path>',
              help="Write the generated nix to <path>.")

@click.option('--index-url', '-i', metavar='<url>',
              help="Base URL of Python Package Index.")
@click.option('--extra-index-url', metavar='<url>',
              help="Extra index URLs to use.")
@click.option('--no-index/--index',
              help="Ignore indexes.")
#@click.option('--find-links', '-f', metavar='<url>',
#              help="Path or url to a package listing/directory.")

#TODO:
# --allow-external <package>  Allow the installation of a package even if it is externally hosted
# --allow-all-external        Allow the installation of all packages that are externally hosted
# --allow-unverified <package>
# Allow the installation of a package even if it is hosted in an insecure and unverifiable way
# --process-dependency-links  Enable the processing of dependency links.

@click.option('--configuration', metavar='<path>',
              help="Read pip2nix configuration from <path>.")

@click.option('--editable', '-e', multiple=True, type=click.Path(),
              metavar='<spec>',
              help="Add a requirement specifier (for pip install compatibility).")
@click.option('--requirement', '-r', multiple=True, type=click.Path(),
              metavar='<file>',
              help="Load specifiers from a requirements file.")
@click.option('--licenses/--no-licenses', default=False,
              help="Extract license information as well, off by default.")
@click.argument('specifiers', nargs=-1)
def generate(specifiers, **kwargs):
    """Generate a .nix file with specified packages."""
    kwargs['specifiers'] = specifiers + kwargs.pop('editable', [])
    kwargs['requirements'] = kwargs.pop('requirement', None)
    kwargs['build_dir'] = kwargs.pop('build')
    kwargs['download_dir'] = kwargs.pop('download')

    config = Config()
    if kwargs['configuration']:
        config.load(kwargs['configuration'])
    else:
        config.find_and_load()
    config.merge_cli_options(kwargs)
    config.validate()

    from pip2nix.main import main
    from pip2nix.generate import generate
    import sys
    generate(config)


@cli.command()
@click.option('--configuration', metavar='<path>',
              help="Read pip2nix configuration from <path>.")
@click.option('--output', metavar='<path>', default='default.nix',
              help="Write the generated file to <path>.")
@click.option('--overrides-output', metavar='<path>',
              default='python-packages-overrides.nix',
              help="Write the generated overrides file to <path>.")
@click.option('--package', metavar='<package>',
              required=True,
              help="Name of the package the scaffold is for.")
def scaffold(output, overrides_output, **kwargs):
    import pip2nix

    config = Config()
    if kwargs['configuration']:
        config.load(kwargs['configuration'])
    else:
        config.find_and_load()
    config.merge_cli_options(kwargs)
    # TODO: Config enforces requirements to be specified, find a nicer
    # way to let Config know that we don't need requirements here.
    config.merge_options({'pip2nix': {'requirements': []}})
    config.validate()

    import jinja2
    raw_template = pkg_resources.resource_string(__name__, 'default.nix.j2')
    t = jinja2.Template(raw_template.decode('utf-8'))
    with open(output, 'w') as f:
        f.write(t.render(
            package_name=kwargs['package'],
            pip2nix_version=pip2nix.__version__))

    overrides_template = pkg_resources.resource_string(
        __name__, 'python-packages-overrides.nix.j2')
    t = jinja2.Template(overrides_template.decode('utf-8'))
    with open(overrides_output, 'w') as f:
        f.write(t.render(
            package_name=kwargs['package'],
            pip2nix_version=pip2nix.__version__))
