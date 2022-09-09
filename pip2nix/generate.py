from __future__ import unicode_literals

from collections import defaultdict
from contexter import Contexter, contextmanager
from tempfile import mkdtemp
from itertools import chain
from operator import attrgetter
from functools import partial
import os
import re
import shutil

from pip._internal.cli import cmdoptions
from pip._internal.cache import WheelCache
from pip._internal.commands.install import InstallCommand
from pip._internal.operations.prepare import RequirementPreparer
from pip._internal.req import RequirementSet
from pip._internal.req.req_tracker import RequirementTracker
from pip._internal.resolution.legacy.resolver import Resolver
from pip._internal.utils.temp_dir import TempDirectory

import pip2nix
from .models.package import PythonPackage, indent
from .models.requirement_set import RequirementSetLayer


flatten = chain.from_iterable


@contextmanager
def temp_dir(name):
    path = mkdtemp('pip2nix')
    yield path
    shutil.rmtree(path)


class NixFreezeCommand(InstallCommand):

    name = 'pip2nix'
    usage = InstallCommand.usage.replace('%prog', name)
    summary = "Generate Nix expressions from requirements."

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

    def __init__(self, pip2nix_config, *args, **kwargs):
        super(NixFreezeCommand, self).__init__(self.name, self.summary,
                                                *args, **kwargs)

        self.config = pip2nix_config
        cmd_opts = self.cmd_opts
        for opt in cmd_opts.option_list:
            if opt.get_opt_string() not in self.PASSED_THROUGH_OPTIONS:
                cmd_opts.remove_option(opt.get_opt_string())

        cmd_opts.add_option('--configuration', metavar='CONFIG',
                            help="Read pip2nix configuration from CONFIG")
        cmd_opts.add_option('--output', metavar='OUTPUT',
                            help="Write the generated Nix to OUTPUT")

    def process_requirements(self, options, requirement_set, finder, resolver):
        if self.config.get_config('pip2nix', 'only_direct'):
            packages_base = [
                r for r in requirement_set.requirements.values()
                if r.is_direct and not r.comes_from.startswith('-c ')]
        else:
            try:
                packages_base = requirement_set.all_requirements
            except AttributeError:
                packages_base = [r for r in requirement_set.requirements.values()]

        # Ensure resolved set
        packages = {
            req.name: PythonPackage.from_requirements(
                req, resolver._discovered_dependencies.get(req.name, []),
                finder, self.config["pip2nix"].get("check_inputs")
            )
            for req in packages_base
            if not req.constraint
        }

        # Ensure setup_requires and test_requires and their dependencies
        while True and not self.config.get_config('pip2nix', 'only_direct'):
            requirements = {}
            for name, package in packages.items():
                for req in (
                    package.setup_requires +
                    package.tests_require +
                    resolver._discovered_dependencies.get(name, [])
                ):
                    if req.name in packages:
                        continue
                    req.is_direct = False
                    requirement_set.add_requirement(req, req.comes_from)
                    requirements[req.name] = req
            requirements.pop('setuptools', None)
            requirements.pop('wheel', None)
            if not requirements:
                break
            finder.format_control.no_binary = set()  # allow binaries
            try:
                resolver.resolve(requirement_set)
            except TypeError:
                indirect_deps = []
                for req in requirement_set.all_requirements:
                    req.is_direct = True
                resolver.resolve(indirect_deps, check_supported_wheels=True)
            for req in requirements.values():
                if not req.source_dir:
                    resolver.resolve([req], check_supported_wheels=True)
                try:
                    packages[req.name] = PythonPackage.from_requirements(
                        requirement_set.requirements[req.name],
                        resolver._discovered_dependencies.get(req.name, []),
                        finder, self.config["pip2nix"].get("check_inputs")
                    )
                except KeyError:
                    req.req.name = req.name.lower()  # try to work around case differences
                    packages[req.name] = PythonPackage.from_requirements(
                        requirement_set.requirements[req.name],
                        resolver._discovered_dependencies.get(req.name, []),
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

    def super_run(self, options, args):
        """Copy of relevant parts from InstallCommand's run()"""

        upgrade_strategy = "eager"
        if options.upgrade:
            upgrade_strategy = options.upgrade_strategy

        with self._build_session(options) as session:
            finder = self._build_package_finder(options, session)
            wheel_cache = WheelCache(options.cache_dir, options.format_control)
            try:
                requirement_set = RequirementSet(
                    require_hashes=options.require_hashes,
                )
                req_tracker_path = False
            except TypeError:  # got an unexpected keyword argument 'require_hashes'
                requirement_set = RequirementSet()
                req_tracker_path = True   # pip 20
            try:
                with TempDirectory(
                    options.build_dir, delete=True, kind="install"
                ) as directory, RequirementTracker(*([directory.path] if req_tracker_path else [])) as req_tracker:
                    try:
                        self.populate_requirement_set(
                            requirement_set, args, options, finder, session,
                            self.name, wheel_cache
                        )
                    except TypeError:
                        self.populate_requirement_set(
                            requirement_set, args, options, finder, session,
                            wheel_cache
                        )
                    except AttributeError:
                        requirement_set = self.get_requirements(
                            args, options, finder, session,
                            wheel_cache
                        )
                    try:
                        preparer = RequirementPreparer(
                            build_dir=directory.path,
                            src_dir=options.src_dir,
                            download_dir=None,
                            wheel_download_dir=None,
                            progress_bar=options.progress_bar,
                            build_isolation=options.build_isolation,
                            req_tracker=req_tracker,
                        )
                    except TypeError:
                        from pip._internal.network.download import Downloader
                        downloader = Downloader(session,
                                                progress_bar=options.progress_bar)
                        preparer = RequirementPreparer(
                            build_dir=directory.path,
                            download_dir=None,
                            src_dir=options.src_dir,
                            wheel_download_dir=None,
                            build_isolation=options.build_isolation,
                            req_tracker=req_tracker,
                            downloader=downloader,
                            finder=finder,
                            require_hashes=options.require_hashes,
                            use_user_site=options.use_user_site,
                        )
                    try:
                        resolver = Resolver(
                            preparer=preparer,
                            finder=finder,
                            session=session,
                            wheel_cache=wheel_cache,
                            use_user_site=options.use_user_site,
                            upgrade_strategy=upgrade_strategy,
                            force_reinstall=options.force_reinstall,
                            ignore_dependencies=options.ignore_dependencies,
                            ignore_requires_python=options.ignore_requires_python,
                            ignore_installed=options.ignore_installed,
                            isolated=options.isolated_mode,
                        )
                    except TypeError:
                        from pip._internal.req.constructors import (
                            install_req_from_req_string,
                        )
                        make_install_req = partial(
                            install_req_from_req_string,
                            isolated=options.isolated_mode,
                            wheel_cache=wheel_cache,
                            use_pep517=options.use_pep517,
                        )
                        try:
                            resolver = Resolver(
                                preparer=preparer,
                                session=session,
                                finder=finder,
                                make_install_req=make_install_req,
                                use_user_site=options.use_user_site,
                                ignore_dependencies=options.ignore_dependencies,
                                ignore_installed=options.ignore_installed,
                                ignore_requires_python=options.ignore_requires_python,
                                force_reinstall=options.force_reinstall,
                                upgrade_strategy=upgrade_strategy,
                            )
                        except TypeError:
                            try:
                                resolver = Resolver(
                                    preparer=preparer,
                                    finder=finder,
                                    make_install_req=make_install_req,
                                    use_user_site=options.use_user_site,
                                    ignore_dependencies=options.ignore_dependencies,
                                    ignore_installed=options.ignore_installed,
                                    ignore_requires_python=options.ignore_requires_python,
                                    force_reinstall=options.force_reinstall,
                                    upgrade_strategy=upgrade_strategy,
                                )
                            except TypeError:
                                make_install_req = partial(
                                    install_req_from_req_string,
                                    isolated=options.isolated_mode,
                                    use_pep517=options.use_pep517,
                                )
                                resolver = Resolver(
                                    preparer=preparer,
                                    finder=finder,
                                    make_install_req=make_install_req,
                                    use_user_site=options.use_user_site,
                                    ignore_dependencies=options.ignore_dependencies,
                                    ignore_installed=options.ignore_installed,
                                    ignore_requires_python=options.ignore_requires_python,
                                    force_reinstall=options.force_reinstall,
                                    upgrade_strategy=upgrade_strategy,
                                    wheel_cache=wheel_cache,
                                )
                    try:
                        resolver.resolve(requirement_set)
                    except TypeError:
                        requirement_set = resolver.resolve(requirement_set, check_supported_wheels=True)
                    finder.format_control.no_binary = set()  # allow binaries
                    self.process_requirements(
                        options,
                        requirement_set,
                        finder,
                        resolver
                    )

            finally:
                try:
                   requirement_set.cleanup_files()
                   wheel_cache.cleanup()
                except AttributeError:
                    # https://github.com/pypa/pip/commit/5cca8f10b304a5a7f3a96dfd66937615324cf826
                    pass

        return requirement_set

    def run(self, options, _args):
        with Contexter() as ctx:
            self.cleanup = ctx
            options, args = self.prepare_options(options)
            requirement_set = self.super_run(options, args)
            return requirement_set

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


def generate(config):
    cmd = NixFreezeCommand(config)

    return cmd.main([])
