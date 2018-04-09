from __future__ import unicode_literals

from collections import defaultdict
from contexter import Contexter, contextmanager
from tempfile import mkdtemp
from itertools import chain
from operator import attrgetter
import os
import shutil

import pip
from pip import cmdoptions
from pip.utils.build import BuildDirectory
from pip.req import InstallRequirement
from pip.wheel import WheelCache
from pip.req import RequirementSet

import pip2nix
from .models.package import PythonPackage, indent
from .models.requirement_set import RequirementSetLayer


flatten = chain.from_iterable


@contextmanager
def temp_dir(name):
    path = mkdtemp('pip2nix')
    yield path
    shutil.rmtree(path)


class NixFreezeCommand(pip.commands.InstallCommand):

    name = 'pip2nix'
    usage = pip.commands.InstallCommand.usage.replace('%prog', name)
    summary = "Generate Nix expressions from requirements."

    PASSED_THROUGH_OPTIONS = (
        '--editable',
        '--requirement',
        '--build',
        '--download',
        '--download-cache',
        '--src',
        '--pre',
    )

    def __init__(self, pip2nix_config, *args, **kwargs):
        super(NixFreezeCommand, self).__init__(*args, **kwargs)
        self.config = pip2nix_config
        cmd_opts = self.cmd_opts
        for opt in cmd_opts.option_list:
            if opt.get_opt_string() not in self.PASSED_THROUGH_OPTIONS:
                cmd_opts.remove_option(opt.get_opt_string())

        cmd_opts.add_option('--configuration', metavar='CONFIG',
                            help="Read pip2nix configuration from CONFIG")
        cmd_opts.add_option('--output', metavar='OUTPUT',
                            help="Write the generated Nix to OUTPUT")

    def process_requirements(self, options, requirement_set, finder):
        top_levels = [r for r in requirement_set.requirements.values()
                      if r.comes_from is None]
        if self.config.get_config('pip2nix', 'only_direct'):
            packages_base = [
                r for r in requirement_set.requirements.values()
                if r.is_direct and not r.comes_from.startswith('-c ')]
        else:
            packages_base = requirement_set.requirements.values()
        packages = {
            req.name: PythonPackage.from_requirements(
                req, requirement_set._dependencies[req])
            for req in packages_base
            if not req.constraint
        }

        devDeps = defaultdict(list)
        with BuildDirectory(options.build_dir, delete=True):
            for req in top_levels:
                raw_tests_require = req.egg_info_data('tests_require.txt')
                if not raw_tests_require:
                    continue
                packages[req.name].check = True
                test_req_lines = filter(None, raw_tests_require.splitlines())
                for test_req_line in test_req_lines:
                    test_req = InstallRequirement.from_line(test_req_line)
                    devDeps[req.name].append(test_req)

            # TODO: this should be per-package
            # see https://github.com/ktosiek/pip2nix/issues/1#issuecomment-113716703
            test_req_set = self.get_tests_requirements_set(
                requirement_set, finder, flatten(devDeps.values()))

            for k, reqs in devDeps.items():
                test_deps = []
                for d in reqs:
                    if requirement_set.has_requirement(d.name):
                        test_deps.append((d.name, None))
                    else:
                        d.get_dist()
                        test_deps.append((d.name, d.pkg_info()['Version']))
                packages[k].test_dependencies = test_deps

            test_packages = {
                req.name: PythonPackage.from_requirements(
                    req, test_req_set._dependencies[req])
                for req in test_req_set.requirements.values()
                if not requirement_set.has_requirement(req.name)
            }

            for package in chain(packages.values(), test_packages.values()):
                pkg_config = self.config.get_package_config(package.name)
                if pkg_config:
                    package.override(pkg_config)

            include_lic = self.config['pip2nix']['licenses']

            with open(self.config['pip2nix']['output'], 'w') as f:
                self._write_about_comment(f)
                f.write('{ pkgs, fetchurl, fetchgit, fetchhg }:\n\n')
                f.write('self: super: {\n')
                f.write('  ' + indent(2, '\n'.join(
                    '"{}" = {}'.format(pkg.name,
                                     pkg.to_nix(include_lic=include_lic))
                    for pkg in sorted(packages.values(),
                                      key=attrgetter('name'))
                )))

                f.write('\n\n### Test requirements\n\n')
                f.write('  ' + indent(2, '\n'.join(
                    '{} = {}'.format(pkg.name,
                                     pkg.to_nix(include_lic=include_lic))
                    for pkg in sorted(test_packages.values(),
                                      key=attrgetter('name'))
                )))

                f.write('\n}\n')

    def _write_about_comment(self, target):
        target.write('# Generated by pip2nix {}\n'.format(pip2nix.__version__))
        target.write('# See https://github.com/johbo/pip2nix\n\n')

    def get_tests_requirements_set(self, base_set, finder, test_dependencies):
        test_req_set = RequirementSetLayer(base=base_set)
        for dep in test_dependencies:
            test_req_set.add_requirement(dep)
        test_req_set.prepare_files(finder)
        return test_req_set

    def super_run(self, options, args):
        """Copy of relevant parts from InstallCommand's run()"""
        temp_target_dir = (self.cleanup << temp_dir('pip2nix-temp-target'))

        with self._build_session(options) as session:
            finder = self._build_package_finder(options, session)
            wheel_cache = WheelCache(options.cache_dir, options.format_control)
            with BuildDirectory(options.build_dir, delete=True) as build_dir:
                requirement_set = RequirementSet(
                    build_dir=build_dir,
                    src_dir=options.src_dir,
                    download_dir=options.download_dir,
                    upgrade=options.upgrade,
                    as_egg=options.as_egg,
                    ignore_installed=options.ignore_installed,
                    ignore_dependencies=options.ignore_dependencies,
                    force_reinstall=options.force_reinstall,
                    use_user_site=options.use_user_site,
                    target_dir=temp_target_dir,
                    session=session,
                    pycompile=options.compile,
                    isolated=options.isolated_mode,
                    wheel_cache=wheel_cache,
                )

                self.populate_requirement_set(
                    requirement_set, args, options, finder, session, self.name,
                    wheel_cache
                )

                requirement_set.prepare_files(finder)

                self.process_requirements(options, requirement_set, finder)

                requirement_set.cleanup_files()

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
                ('index_url', ('index_url', )),
                ('output', ('output', )),
                ('build', ('build', )),
                ('download', ('download',)),
                ('find_links', ('find_links', )),
                ('src', ('src',))]:
            value = self.config.get_config('pip2nix', *path)
            if value is not None:
                setattr(options, opt_name, value)

        requirements = defaultdict(list)
        for req_type, req in self.config.get_requirements():
            requirements[req_type].append(req)

        args = requirements[None]
        options.requirements = requirements['-r']

        options.no_install = True  # Download only
        options.upgrade = True  # Download all packages
        options.use_wheel = False  # We'll build the wheels ourself
        options.no_clean = True  # This is needed to access pkg_info later
        options.download_dir = self.config.get_config('pip2nix', 'download') \
            or (self.cleanup << temp_dir('pip2nix'))
        options.constraints = self.config.get_constraints()

        # TODO: What are those about/for?
        cmdoptions.resolve_wheel_no_use_binary(options)
        cmdoptions.check_install_build_global(options)

        options.ignore_installed = True
        src_dir = self.config.get_config('pip2nix', 'src')
        options.src_dir = os.path.abspath(src_dir) if src_dir else None

        return options, args


def generate(config):
    cmd = NixFreezeCommand(config)

    return cmd.main([])
