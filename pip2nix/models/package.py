import os


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
            'super.buildPythonPackage {{',
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
