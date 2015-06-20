from contextlib import contextmanager
from collections import defaultdict
from copy import deepcopy
import os
from tempfile import mkdtemp
import shutil
import sys

import pip
from pip import cmdoptions
from pip.utils.build import BuildDirectory
import pip.commands
from pip.req import InstallRequirement
from pip.req import RequirementSet
from pip.wheel import WheelCache


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

    def process_requirements(self, options, requirement_set, test_req_set, finder):
        ctxs = {
            req.name: self._generate_nix_ctx(req, requirement_set._dependencies[req])
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
                ctxs[req.name]['doCheck'] = 'true'
                test_req_lines = filter(None, raw_tests_require.splitlines())
                for test_req_line in test_req_lines:
                    test_req = InstallRequirement.from_line(test_req_line)
                    test_req_set.add_requirement(test_req)
                    devDeps[req.name].append(test_req)

            requirement_set.cleanup_files()

            test_req_set.prepare_files(finder)

            for k, reqs in devDeps.items():
                ctxs[k]['devBuildInputs'] = ' '.join(r.name for r in reqs)

            f = open('python-packages.nix', 'w')
            f.write('{\n')
            f.write('  ' + indent(2, '\n'.join(
                self._generate_nix_expr(ctx)
                for ctx in ctxs.values()
            )))

            f.write('\n\n### Test requirements\n\n')
            f.write('  ' + indent(2, '\n'.join(
                self._generate_nix(req, test_req_set._dependencies[req])
                for req in test_req_set.requirements.values()
                if not requirement_set.has_requirement(req.name)
            )))

        f.write('\n}\n')

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
                test_requirement_set = RequirementSet(
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

                self.process_requirements(options, requirement_set, test_requirement_set, finder)

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

        try:
            requirement_set = self.super_run(options, args)
            return requirement_set
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir)

    def _generate_nix(self, requirement, deps):
        return self._generate_nix_expr(self._generate_nix_ctx(requirement, deps))

    def _generate_nix_ctx(self, requirement, deps):
        link = requirement.link
        pkg_info = requirement.pkg_info()

        buildInputs = [d.name for d in deps]
        devBuildInputs = []  # TODO
        if link.scheme == 'file':
            sourceExpr = './' + os.path.relpath(requirement.link.path)
        elif link.scheme in ('http', 'https'):
            sourceExpr = '\n'.join((
                'fetchurl {{',
                '  url = "{url}";',
                '  {hash_name} = "{hash}";',
                '}}'
            )).format(
                url=link.url.split('#', 1)[0],
                hash=link.hash,
                hash_name=link.hash_name,
            )
        return dict(
            name=requirement.name,
            doCheck='false',
            version=pkg_info['Version'],
            sourceExpr=indent(2, sourceExpr),
            buildInputs=' '.join(buildInputs),
            devBuildInputs='',
        )

    def _generate_nix_expr(self, context):
        template = '\n'.join((
            '{name} = self.buildPythonPackage {{',
            '  doCheck = {doCheck};',
            '  name = "{name}-{version}";',
            '  src = {sourceExpr};',
            '  propagatedBuildInputs = with self; [{buildInputs}];',
            '  buildInputs = with self; [{devBuildInputs}];',
            '}};',
        ))

        return template.format(
            **context
        )

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    cmd = NixFreezeCommand()

    return cmd.main(args)


if __name__ == '__main__':
    sys.exit(main())
