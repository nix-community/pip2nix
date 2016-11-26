import json
import os
from subprocess import check_output

from subprocess import check_output


_nix_licenses = None


def get_nix_licenses():
    """
    Generate a map of known licenses based on `nixpkgs`.
    """
    global _nix_licenses

    if _nix_licenses is None:
        nix_licenses_json = check_output([
            'nix-instantiate', '--eval', '--expr',
            'with import <nixpkgs> { }; builtins.toJSON lib.licenses'])
        nix_licenses_json = nix_licenses_json.decode('utf-8')

        # Dictionary which contains the contents of nixpkgs.lib.licenses.
        _nix_licenses = json.loads(json.loads(nix_licenses_json))

        # Convert all values to lowercase.
        for entry in _nix_licenses.values():
            for key, value in entry.items():
                try:
                    entry[key] = value.lower()
                except AttributeError:
                    # Skip values which don't have a lower() function.
                    pass

    return _nix_licenses


# Mapping from license name in setup.py to attribute in nixpkgs.lib.licenses.
# TODO: Think about providing this from outside, maybe from a file.
case_sensitive_license_nix_map = {
    'Apache 2.0': 'asl20',
    'Apache License, Version 2.0': 'asl20',
    'Apache Software License': 'asl20',
    'BSD license': 'bsdOriginal',
    'BSD': 'bsdOriginal',
    'GNU GPL': 'gpl1',
    'GNU GPLv2 or any later version': 'gpl2Plus',
    'GNU General Public License (GPL)': 'gpl1',
    'GNU General Public License v2 or later (GPLv2+)': 'gpl2Plus',
    'GPL': 'gpl1',
    'GPLv2 or later': 'gpl2Plus',
    'GPLv2': 'gpl2',
    'GPLv3': 'gpl3',
    'LGPLv2.1 or later': 'lgpl21Plus',
    'PSF License': 'psfl',
    'PSF': 'psfl',
    'Python Software Foundation License': 'psfl',
    'Python style': 'psfl',
    'Two-clause BSD license': 'bsd2',
    'ZPL 2.1': 'zpt21',
    'ZPL': 'zpt21',
    'Zope Public License': 'zpt21',
}
license_nix_map = {name.lower(): nix_attr
                   for name, nix_attr in
                   case_sensitive_license_nix_map.items()}


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
        if meta_args:
            raw_meta_args = ''
            for k, v in sorted(meta_args.items()):
                raw_meta_args += '{} = {};\n'.format(k, v)
            meta = meta_template.format(meta_args=indent(2, raw_meta_args))
            raw_args += '\n{}'.format(meta)

        return template.format(args=indent(2, raw_args))

    def get_license_nix(self):
        licenses = self.get_licenses_from_pkginfo()

        # Convert license strings to nix.
        nix_licenses = set()
        for lic in licenses:
            nix_licenses.add(license_to_nix(lic))

        template = '[ {licenses} ]'
        return template.format(licenses=' '.join(nix_licenses))

    def get_licenses_from_pkginfo(self):
        """
        Parses the license string from PKG-INFO file.
        """
        licenses = set()
        data = self.pip_req.egg_info_data('PKG-INFO')

        for line in data.split('\n'):

            # License string from setup() function.
            if line.startswith('License: '):
                lic = line.split('License: ')[-1]
                licenses.add(lic.strip())

            # License strings from classifiers.
            elif line.startswith('Classifier: License ::'):
                lic = line.split('::')[-1]
                licenses.add(lic.strip())

        return filter_licenses(licenses)


def filter_licenses(licenses):
    exclude = set(['UNKNOWN'])
    return licenses - exclude


def license_to_nix(license_name, nixpkgs='pkgs'):
    template = '{nixpkgs}.lib.licenses.{attribute}'
    full_name_template = '{{ fullName = "{full_name}"; }}'

    # Convert to lowercase for searching.
    full_name = license_name
    license_name = license_name.lower()

    # First try to fetch nix attribute name from custom mapping.
    attr = license_nix_map.get(license_name)
    if attr:
        return template.format(nixpkgs=nixpkgs, attribute=attr)

    # Otherwise try to look it up in the nix licenses.
    for attr, nix_license_data in get_nix_licenses().items():
        if license_name in nix_license_data.values():
            return template.format(nixpkgs=nixpkgs, attribute=attr)

    # No luck converting the license name to an attribute in
    # nixpkgs.lib.licenses. In this case we can at least store a set with the
    # fullName attribute like sets in nixpkgs.lib.licenses.
    return full_name_template.format(full_name=full_name)


def link_to_nix(link):
    if link.scheme == 'file':
        return './' + os.path.relpath(link.path)
    elif link.scheme in ('http', 'https'):
        hash = prefetch_url(link.url_without_fragment)
        return '\n'.join((
            'fetchurl {{',
            '  url = "{url}";',
            '  {hash_name} = "{hash}";',
            '}}'
        )).format(
            url=link.url.split('#', 1)[0],
            hash=hash,
            hash_name='sha256',
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
        raise NotImplementedError(
            'Unknown link shceme "{}"'.format(link.scheme))


def prefetch_git(url, rev):
    if len(rev) == 40 and rev.isdigit():
        rev_args = ['--rev', rev]
    else:
        rev_args = ['--branch-name', rev]
    out = check_output(['nix-prefetch-git'] + rev_args + [url])
    data = json.loads(out.decode('utf-8'))
    return data['sha256'], data['rev']


def prefetch_url(url):
    out = check_output(['nix-prefetch-url', url])
    data = out.decode('utf-8').strip()
    return data
