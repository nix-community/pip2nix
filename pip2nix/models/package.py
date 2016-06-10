import json
import os

from subprocess import check_output


# TODO: Seems not very nice to do this here, maybe there is a better place
# during app startup. And only executing when licenses flag is set.
NIX_LICENSES_JSON = check_output([
    'nix-instantiate', '--eval', '--expr',
    'with import <nixpkgs> { }; builtins.toJSON lib.licenses'])

# Dictionary which contains the contents of nixpkgs.lib.licenses.
nix_licenses = json.loads(json.loads(NIX_LICENSES_JSON))

# Mapping from license name in setup.py to attribute in nixpkgs.lib.licenses.
LICENSE_NIX_MAP = {
    'MIT': 'mit',
    'ZPL 2.1': 'zpt21',
}

# Mapping to rename unresolved license names from setup.py files.
LICENSE_RENAME_MAP = {
}


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


class PythonPackage(object):
    def __init__(self, name, version, dependencies, source, pip_req):
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
        self.pip_req = pip_req

    @classmethod
    def from_requirements(cls, req, deps):
        pkg_info = req.pkg_info()

        def name_version(dep):
            return (
                dep.name,
                dep.pkg_info()['Version'] if dep.source_dir else None,
            )

        return cls(
            name=req.name,
            version=pkg_info['Version'],
            dependencies=[name_version(d) for d in deps],
            source=req.link,
            pip_req=req,
        )

    def override(self, config):
        self.raw_args = config.get('args', {})

    def to_nix(self, include_lic):
        template = '\n'.join((
            'super.buildPythonPackage {{',
            '  {args}',
            '}};',
        ))
        meta_template = '\n'.join((
            'meta = {{',
            '  {meta_args}',
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

        # Prepare meta arguments.
        meta_args = dict()
        if include_lic:
            license_nix = self.get_license_nix()
            if license_nix:
                meta_args['license'] = license_nix

        # Render name first
        raw_args = 'name = {};'.format(args.pop('name'))
        for k, v in sorted(args.items()):
            raw_args += '\n{} = {};'.format(k, v)

        # Render meta arguments.
        raw_meta_args = ''
        for k, v in sorted(meta_args.items()):
            raw_meta_args += '{} = {};\n'.format(k, v)
        meta = meta_template.format(meta_args=indent(2, raw_meta_args))
        raw_args += '\n{}'.format(meta)

        return template.format(args=indent(2, raw_args))

    def get_license_nix(self):
        license_str = self.get_license_string()
        if license_str:
            return license_to_nix(license_str)

    def get_license_string(self):
        """
        Returns the license string set in setup.py as license argument to
        setup or as classifier.
        License argument takes precedence.
        """
        # TODO: Would be cool to get the info directly from setup.py
        # but some setup.py scripts contain too much magic for run_setup()
        #
        # This was my approach to load it:
        # from distutils import core
        # print self.pip_req.setup_py
        # dist = core.run_setup(self.pip_req.setup_py, stop_after='init')
        # lic = dist.get_license()

        data = self.pip_req.egg_info_data('PKG-INFO')

        for line in data.split('\n'):

            # Parse license from license argument.
            if line.startswith(u'License: '):
                lic = line.split('License: ')[-1]
                lic = lic.strip()
                if lic not in ['UNKNOWN']:
                    return lic

            # Parse license from classifiers.
            elif line.startswith(u'Classifier: License ::'):
                lic = line.split('::')[-1]
                lic = lic.strip()
                return lic


def license_to_nix(license_name, nixpkgs='pkgs'):
    template = '{nixpkgs}.lib.licenses.{attribute}'
    full_name_template = '{{ fullName = "{full_name}"; }}'

    # First try to fetch from custom mapping.
    if license_name in LICENSE_NIX_MAP:
        attr = LICENSE_NIX_MAP.get(license_name)
        return template.format(nixpkgs=nixpkgs, attribute=attr)

    # Otherwise try to lookup in licenses from nix.
    for attr, nix_license_data in nix_licenses.items():
        if license_name in nix_license_data.values():
            return template.format(nixpkgs=nixpkgs, attribute=attr)

    # Had no luck converting the license name to a license in
    # nixpkgs.lib.licenses. In this case we can at least store a set with
    # the fullName attribute like in nix licenses.
    license_name = LICENSE_RENAME_MAP.get(license_name, license_name)
    return full_name_template.format(full_name=license_name)


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
