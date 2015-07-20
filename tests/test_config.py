from pip2nix.config import Config


class MiniMock(object):
    def __init__(self):
        self.__calls = []

    def __getitem__(self, value):
        return CallableMiniMock(value, self)


class CallableMiniMock(object):
    def __init__(self, name, parent):
        self.__calls = parent._MiniMock_calls
        self.__name = name

    def __call__(self, *args, **kwargs):
        self.__calls.append((args, kwargs))


def test_merging_configs():
    c = Config()
    c.merge_options({'optA': 'A', 'optB': 'B'})
    c.merge_options({'optA': 'A2'})
    assert c['optA'] == 'A2'
    assert c['optB'] == 'B'


def test_loading_requirements_from_cli():
    c = Config()
    opts = MiniMock()
    opts.requirements = ['requirements.txt']
    opts.editables = ['.']
    c.merge_cli_options(opts, ['other_package'])
    assert c['pip2nix']['requirements'] == \
        ['other_package', '-e .', '-r requirements.txt']


def test_get_requirements():
    c = Config()
    c.merge_options({'pip2nix': {
        'requirements': ['simple', '-rreqs.txt', '-e editable']}})
    assert list(c.get_requirements()) == \
        [(None, 'simple'), ('-r', 'reqs.txt'), ('-e', 'editable')]
