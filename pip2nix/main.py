from __future__ import print_function, unicode_literals

from contextlib import contextmanager
from collections import defaultdict
from copy import deepcopy
from itertools import chain
import os
from tempfile import mkdtemp
from subprocess import check_output
import shutil
import sys

import pip
from pip import cmdoptions
from pip.utils.build import BuildDirectory
import pip.commands
from pip.req import InstallRequirement
from pip.req import RequirementSet
from pip.wheel import WheelCache

from .config import Config


flatten = chain.from_iterable


class RequirementSetLayer(RequirementSet):
    def __init__(self, *args, **kwargs):
        self.base_requirement_set = kwargs.pop('base')
        kwargs.setdefault('build_dir', self.base_requirement_set.build_dir)
        kwargs.setdefault('src_dir', self.base_requirement_set.src_dir)
        kwargs.setdefault('download_dir', self.base_requirement_set.download_dir)
        kwargs.setdefault('upgrade', self.base_requirement_set.upgrade)
        kwargs.setdefault('as_egg', self.base_requirement_set.as_egg)
        kwargs.setdefault('ignore_installed', self.base_requirement_set.ignore_installed)
        kwargs.setdefault('ignore_dependencies', self.base_requirement_set.ignore_dependencies)
        kwargs.setdefault('force_reinstall', self.base_requirement_set.force_reinstall)
        kwargs.setdefault('use_user_site', self.base_requirement_set.use_user_site)
        kwargs.setdefault('target_dir', self.base_requirement_set.target_dir)
        kwargs.setdefault('session', self.base_requirement_set.session)
        kwargs.setdefault('pycompile', self.base_requirement_set.pycompile)
        kwargs.setdefault('isolated', self.base_requirement_set.isolated)
        kwargs.setdefault('wheel_cache', self.base_requirement_set._wheel_cache)
        super(RequirementSetLayer, self).__init__(*args, **kwargs)

    def _prepare_file(self, finder, req_to_install):
        if self.base_requirement_set.has_requirement(req_to_install.name):
            print('Package {} available in base ReqSet'.format(req_to_install.name))
            base_req = self.base_requirement_set.requirements[req_to_install.name]
            base_pkg_info = base_req.pkg_info()
            if not req_to_install.specifier.contains(base_pkg_info['Version']):
                # TODO: exceptions
                raise AssertionError(
                    ('There is already {req_name}=={base_pkg_version} downloaded, '
                     'but {comes_from} requires {req_name}{req_spec}')
                    .format(
                        req_name=req_to_install.name,
                        req_spec=req_to_install.specifier,
                        base_pkg_version=base_pkg_info['Version'],
                        comes_from=req_to_install.comes_from.name))
            return []
        else:
            extras = super(RequirementSetLayer, self) \
                ._prepare_file(finder, req_to_install)
            return extras


def indent(amount, string):
    lines = string.splitlines()
    if len(lines) == 0:
        return ''
    elif len(lines) == 1:
        return lines[0]
    else:
        return (
            lines[0] + '\n' +
            '\n'.join(' ' * amount + l for l in lines[1:]))


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

    def __init__(self, *args, **kwargs):
        super(NixFreezeCommand, self).__init__(*args, **kwargs)
        cmd_opts = self.cmd_opts
        for opt in cmd_opts.option_list:
            if opt.get_opt_string() not in self.PASSED_THROUGH_OPTIONS:
                cmd_opts.remove_option(opt.get_opt_string())

        cmd_opts.add_option('--configuration', metavar='CONFIG',
                            help="Read pip2nix configuration from CONFIG")
        cmd_opts.add_option('--output', metavar='OUTPUT',
                            help="Write the generated Nix to OUTPUT")

    def process_requirements(self, options, requirement_set, finder):
        packages = {
            req.name: PythonPackage.from_requirements(
                req, requirement_set._dependencies[req])
            for req in requirement_set.requirements.values()
        }

        devDeps = defaultdict(list)
        with BuildDirectory(options.build_dir, delete=True) as build_dir:
            top_levels = [r for r in requirement_set.requirements.values()
                            if r.comes_from is None]
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

            f = open(self.config['pip2nix']['output'], 'w')
            f.write('{\n')
            f.write('  ' + indent(2, '\n'.join(
                '{} = {}'.format(pkg.name, pkg.to_nix())
                for pkg in packages.values()
            )))

            f.write('\n\n### Test requirements\n\n')
            f.write('  ' + indent(2, '\n'.join(
                '{} = {}'.format(pkg.name, pkg.to_nix())
                for pkg in test_packages.values()
            )))

        f.write('\n}\n')

    def get_tests_requirements_set(self, base_set, finder, test_dependencies):
        test_req_set = RequirementSetLayer(base=base_set)
        for dep in test_dependencies:
            test_req_set.add_requirement(dep)
        test_req_set.prepare_files(finder)
        return test_req_set

    def super_run(self, options, args):
        """Copy of relevant parts from InstallCommand's run()"""
        # TODO: What are those about/for?
        cmdoptions.resolve_wheel_no_use_binary(options)
        cmdoptions.check_install_build_global(options)

        options.ignore_installed = True
        options.src_dir = os.path.abspath(options.src_dir)

        index_urls = [options.index_url] + options.extra_index_urls

        temp_target_dir = mkdtemp()

        with self._build_session(options) as session:
            finder = self._build_package_finder(options, index_urls, session)
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
        
    def run(self, options, args):
        options.no_install = True  # Download only
        options.upgrade = True  # Download all packages
        options.use_wheel = False  # We'll build the wheels ourself
        options.no_clean = True  # This is needed to access pkg_info later
        # TODO: what if InstallCommand.run fails?
        if options.download_dir:
            tmpdir = None
        else:
            options.download_dir = tmpdir = mkdtemp('pip2nix')

        self.config = Config()
        if options.configuration:
            self.config.load(options.configuration)
        else:
            self.config.find_and_load()
        self.config.merge_cli_options(options, args)
        self.config.validate()

        args = []
        options.editables = []
        options.requirements = []
        for req_type, req_name in self.config.get_requirements():
            if req_type == '-e':
                options.editables.append(req_name)
            elif req_type == '-r':
                options.requirements.append(req_name)
            elif req_type is None:
                args.append(req_name)

        try:
            requirement_set = self.super_run(options, args)
            return requirement_set
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir)


class PythonPackage(object):
    def __init__(self, name, version, dependencies, source):
        """
        :param dependencies: list of (name, version) pairs.
        """
        self.name = name
        self.version = version
        self.dependencies = dependencies
        self.raw_args = {}
        self.source = source
        self.check = False
        self.test_dependencies = None

    @classmethod
    def from_requirements(cls, req, deps):
        pkg_info = req.pkg_info()

        return cls(
            name=req.name,
            version=pkg_info['Version'],
            dependencies=[(d.name, d.pkg_info()['Version']) for d in deps],
            source=req.link,
        )

    def override(self, config):
        self.raw_args = config.get('args', {})

    def to_nix(self):
        template = '\n'.join((
            'self.buildPythonPackage {{',
            '  {args}',
            '}};',
        ))

        args = dict(
            name='"{s.name}-{s.version}"'.format(s=self),
            doCheck='true' if self.check else 'false',
            src=link_to_nix(self.source),
            propagatedBuildInputs='with self; [' + (
                ' '.join('{}'.format(name) for name, version
                         in self.dependencies)) + ']',
            buildInputs='with self; [' + (
                ' '.join('{}'.format(name) for name, version
                         in self.test_dependencies or ())) + ']',
        )

        args.update(self.raw_args)

        # Render name first
        raw_args = 'name = {};'.format(args.pop('name'))
        for k, v in args.items():
            raw_args += '\n{} = {};'.format(k, v)

        return template.format(args=indent(2, raw_args))


def link_to_nix(link):
    if link.scheme == 'file':
        return './' + os.path.relpath(link.path)
    elif link.scheme in ('http', 'https'):
        return '\n'.join((
            'fetchurl {{',
            '  url = "{url}";',
            '  {hash_name} = "{hash}";',
            '}}'
        )).format(
            url=link.url.split('#', 1)[0],
            hash=link.hash,
            hash_name=link.hash_name,
        )
    elif link.scheme.startswith('git+'):
        url = link.url[len('git+'):]
        url = url.split('#', 1)[0]
        url, branch = url.rsplit('@', 1)
        print('Prefetching', url, 'at revision', branch)
        hash, revision = prefetch_git(url, branch)
        return '\n'.join((
            'fetchgit {{',
            '  url = "{url}";',
            '  rev = "{revision}";',
            '  sha256 = "{hash}";',
            '}}',
        )).format(
            url=url,
            revision=revision,
            hash=hash,
        )
    else:
        raise NotImplementedError('Unknown link shceme "{}"'.format(link.scheme))


def prefetch_git(url, rev):
    if len(rev) == 40 and rev.isdigit():
        rev_args = ['--rev', rev]
    else:
        rev_args = ['--branch-name', rev]
    out = check_output(['nix-prefetch-git'] + rev_args + [url])
    for line in out.splitlines():
        if line.startswith('git revision is '):
            rev = line.rsplit(' ', 1)[-1]
        last_line = line

    return last_line, rev


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    cmd = NixFreezeCommand()

    return cmd.main(args)


if __name__ == '__main__':
    sys.exit(main())
