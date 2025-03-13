from __future__ import unicode_literals

from collections import defaultdict
from contexter import Contexter, contextmanager
from tempfile import mkdtemp
from itertools import chain
from operator import attrgetter
from functools import partial
from typing import List, Optional
import os
import re
import shutil

from pip._internal.cli import cmdoptions
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.cli.cmdoptions import make_target_python
from pip._internal.cli.req_command import (
    with_cleanup,
    warn_if_run_as_root,
)
from pip._internal.cache import WheelCache
from pip._internal.commands.install import (
    create_os_error_message,
    decide_user_install,
    get_check_binary_allowed,
    InstallCommand,
    reject_location_related_install_options,
)
from pip._internal.exceptions import CommandError, InstallationError
from pip._internal.operations.build.build_tracker import get_build_tracker
from pip._internal.operations.prepare import RequirementPreparer
from pip._internal.req import RequirementSet
# TODO: fixme
# from pip._internal.req.req_tracker import RequirementTracker
from pip._internal.resolution.legacy.resolver import Resolver
from pip._internal.utils.logging import getLogger
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.misc import (
    get_pip_version,
    protect_pip_from_modification_on_windows,
)
from pip._internal.wheel_builder import (
    build,
    should_build_for_install_command,
)

import pip2nix
from .models.package import PythonPackage, indent
from .models.requirement_set import RequirementSetLayer


flatten = chain.from_iterable

logger = getLogger(__name__)


@contextmanager
def temp_dir(name):
    path = mkdtemp('pip2nix')
    yield path
    shutil.rmtree(path)


class NixFreezeCommand(InstallCommand):
    """
    Freeze dependencies to Nix.

    Discovering all dependencies does traditionally mean running the
    installation procedure to capture all potentially dynamic requirements.
    This is why this class does inherit from ``InstallCommand``.
    """

    PASSED_THROUGH_OPTIONS = (
        '--build',
        '--download',
        '--download-cache',
        '--editable',
        '--no-binary',
        '--pre',
        '--requirement',
        '--src',
    )

    def add_options(self) -> None:
        """Configure pip2nix specific options."""
        super().add_options()
        self._remove_not_passed_through_options()
        cmd_opts = self.cmd_opts
        cmd_opts.add_option('--configuration', metavar='CONFIG',
                            help="Read pip2nix configuration from CONFIG")
        cmd_opts.add_option('--output', metavar='OUTPUT',
                            help="Write the generated Nix to OUTPUT")

    def _remove_not_passed_through_options(self) -> None:
        cmd_opts = self.cmd_opts
        for opt in cmd_opts.option_list:
            if opt.get_opt_string() not in self.PASSED_THROUGH_OPTIONS:
                cmd_opts.remove_option(opt.get_opt_string())

    def __init__(self, pip2nix_config, name, summary, *args, **kwargs):
        super(NixFreezeCommand, self).__init__(name, summary, *args, **kwargs)
        self.config = pip2nix_config

    def run(self, options, _args):
        with Contexter() as ctx:
            self.cleanup = ctx
            options, args = self.prepare_options(options)
            return self.super_run(options, args)

    def prepare_options(self, options):
        """Load configuration from self.config into pip options.

        Returns a (options, args) tuple."""
        for opt_name, path in [
                ('build', ('build', )),
                ('download', ('download',)),
                ('index_url', ('index_url', )),
                ('no_binary', ('no_binary', )),
                ('output', ('output', )),
                ('src', ('src',))]:
            value = self.config.get_config('pip2nix', *path)
            if value is not None:
                setattr(options, opt_name, value)

        requirements = defaultdict(list)
        for req_type, req in self.config.get_requirements():
            requirements[req_type].append(req)

        args = requirements[None]
        options.requirements = requirements['-r']
        options.format_control.no_binary = set(options.no_binary)
        options.no_install = True  # Download only
        options.upgrade = True  # Download all packages
        options.use_wheel = False  # We'll build the wheels ourself
        options.no_clean = True  # This is needed to access pkg_info later
        options.download_dir = self.config.get_config('pip2nix', 'download') \
            or (self.cleanup << temp_dir('pip2nix'))
        options.constraints = self.config.get_constraints()

        # TODO: What are those about/for?
        cmdoptions.check_install_build_global(options)

        options.ignore_installed = True
        src_dir = self.config.get_config('pip2nix', 'src')
        options.src_dir = os.path.abspath(src_dir) if src_dir else None

        return options, args

    @with_cleanup
    def super_run(self, options, args):
        """
        Copy of relevant parts from InstallCommand's ``run()``.

        The basic idea is that a very similar behavior to the run method is
        required. Basically everything except the actual installation is
        needed.

        At the end of this method a call to ``process_requirements`` is made,
        so that the discovered dependencies will be rendered into a Nix file.
        """
        if options.use_user_site and options.target_dir is not None:
            raise CommandError("Can not combine '--user' and '--target'")

        cmdoptions.check_install_build_global(options)
        upgrade_strategy = "to-satisfy-only"
        if options.upgrade:
            upgrade_strategy = options.upgrade_strategy

        cmdoptions.check_dist_restriction(options, check_target=True)

        logger.verbose("Using %s", get_pip_version())
        options.use_user_site = decide_user_install(
            options.use_user_site,
            prefix_path=options.prefix_path,
            target_dir=options.target_dir,
            root_path=options.root_path,
            isolated_mode=options.isolated_mode,
        )

        target_temp_dir: Optional[TempDirectory] = None
        if options.target_dir:
            options.ignore_installed = True
            options.target_dir = os.path.abspath(options.target_dir)
            if (
                # fmt: off
                os.path.exists(options.target_dir) and
                not os.path.isdir(options.target_dir)
                # fmt: on
            ):
                raise CommandError(
                    "Target path exists but is not a directory, will not continue."
                )

            # Create a target directory for using with the target option
            target_temp_dir = TempDirectory(kind="target")
            self.enter_context(target_temp_dir)

        session = self.get_default_session(options)

        target_python = make_target_python(options)
        finder = self._build_package_finder(
            options=options,
            session=session,
            target_python=target_python,
            ignore_requires_python=options.ignore_requires_python,
        )
        wheel_cache = WheelCache(options.cache_dir, options.format_control)

        build_tracker = self.enter_context(get_build_tracker())

        directory = TempDirectory(
            delete=not options.no_clean,
            kind="install",
            globally_managed=True,
        )

        try:
            reqs = self.get_requirements(args, options, finder, session)

            # Only when installing is it permitted to use PEP 660.
            # In other circumstances (pip wheel, pip download) we generate
            # regular (i.e. non editable) metadata and wheels.
            for req in reqs:
                req.permit_editable_wheels = True

            reject_location_related_install_options(reqs, options.install_options)

            preparer = self.make_requirement_preparer(
                temp_build_dir=directory,
                options=options,
                build_tracker=build_tracker,
                session=session,
                finder=finder,
                use_user_site=options.use_user_site,
                verbosity=self.verbosity,
            )
            resolver = self.make_resolver(
                preparer=preparer,
                finder=finder,
                options=options,
                wheel_cache=wheel_cache,
                use_user_site=options.use_user_site,
                ignore_installed=options.ignore_installed,
                ignore_requires_python=options.ignore_requires_python,
                force_reinstall=options.force_reinstall,
                upgrade_strategy=upgrade_strategy,
                use_pep517=options.use_pep517,
            )

            self.trace_basic_info(finder)

            requirement_set = resolver.resolve(
                reqs, check_supported_wheels=not options.target_dir
            )

            try:
                pip_req = requirement_set.get_requirement("pip")
            except KeyError:
                modifying_pip = False
            else:
                # If we're not replacing an already installed pip,
                # we're not modifying it.
                modifying_pip = pip_req.satisfied_by is None
            protect_pip_from_modification_on_windows(modifying_pip=modifying_pip)

        except OSError as error:
            show_traceback = self.verbosity >= 1

            message = create_os_error_message(
                error,
                show_traceback,
                options.use_user_site,
            )
            logger.error(message, exc_info=show_traceback)  # noqa

            return ERROR

        if options.target_dir:
            assert target_temp_dir
            self._handle_target_dir(
                options.target_dir, target_temp_dir, options.upgrade
            )
        if options.root_user_action == "warn":
            warn_if_run_as_root()

        self.process_requirements(
            options,
            requirement_set,
            finder,
            resolver
        )

        return SUCCESS

    def process_requirements(self, options, requirement_set, finder, resolver):
        if self.config.get_config('pip2nix', 'only_direct'):
            packages_base = [
                r for r in requirement_set.requirements.values()
                if r.is_direct and not r.comes_from.startswith('-c ')]
        else:
            packages_base = requirement_set.all_requirements

        def _get_dependencies(req, requirement_set):
            results = []
            for dep in req.get_dist().iter_dependencies():
                install_requirement = requirement_set.get_requirement(dep.name)
                results.append(install_requirement)
            return results

        # Ensure resolved set
        packages = {
            req.name: PythonPackage.from_requirements(
                req, _get_dependencies(req, requirement_set),
                finder, self.config["pip2nix"].get("check_inputs")
            )
            for req in packages_base
            if not req.constraint
        }

        # Ensure setup_requires and test_requires and their dependencies
        if not self.config.get_config('pip2nix', 'only_direct'):
            requirements = {}
            for name, package in packages.items():
                for req in (
                    package.setup_requires +
                    package.tests_require
                ):
                    if req.name in packages:
                        continue
                    req.is_direct = False
                    requirements[req.name] = req
            requirements.pop('setuptools', None)
            requirements.pop('wheel', None)

            # TODO: which value should "check_supported_wheels" really have?
            new_requirement_set = resolver.resolve(
                requirements.values(), check_supported_wheels=True)

            for req in new_requirement_set.all_requirements:
                packages[req.name] = PythonPackage.from_requirements(
                    req,
                    _get_dependencies(req, new_requirement_set),
                    finder, self.config["pip2nix"].get("check_inputs")
                )

        # If you need a newer version of setuptools or wheel, you know it and
        # can add it later; By default these would cause issues.
        packages.pop('setuptools', None)
        packages.pop('wheel', None)

        include_lic = self.config['pip2nix']['licenses']

        cache = ''
        if os.path.exists(self.config['pip2nix']['output']):
            with open(self.config['pip2nix']['output'], 'r') as f:
                cache = f.read()
        cache = re.sub('\s+', ' ', cache, re.M & re.I)
        cache = re.findall('url = "([^"]+)"; sha256 = "([^"]+)"', cache, re.M)
        cache = dict(cache)

        with open(self.config['pip2nix']['output'], 'w') as f:
            self._write_about_comment(f)
            f.write('{ pkgs, fetchurl, fetchgit, fetchhg }:\n\n')
            f.write('self: super: {\n')
            f.write('  ' + indent(2, '\n'.join(
                '"{}" = {}'.format(pkg.name,
                                   pkg.to_nix(include_lic=include_lic,
                                              cache=cache))
                for pkg in sorted(packages.values(),
                                  key=attrgetter('name'))
            )))
            f.write('\n}\n')

    def _write_about_comment(self, target):
        target.write('# Generated by pip2nix {}\n'.format(pip2nix.__version__))
        target.write('# See https://github.com/nix-community/pip2nix\n\n')

    def get_tests_requirements_set(self, base_set, finder, test_dependencies):
        test_req_set = RequirementSetLayer(base=base_set)
        for dep in test_dependencies:
            test_req_set.add_requirement(dep)
        test_req_set.prepare_files(finder)
        return test_req_set


def generate(config):
    """Run the generate command with the given configuration in config."""
    cmd = NixFreezeCommand(
        name="generate",
        summary="Generate Nix expressions from requirements.",
        pip2nix_config=config)

    return cmd.main([])
