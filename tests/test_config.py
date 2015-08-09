import pytest
import os

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


@pytest.yield_fixture
def cwd():
    old_cwd = os.getcwd()
    yield os.chdir
    os.chdir(old_cwd)


def test_merging_configs():
    c = Config()
    c.merge_options({'optA': 'A', 'optB': 'B'})
    c.merge_options({'optA': 'A2'})
    assert c['optA'] == 'A2'
    assert c['optB'] == 'B'


def test_loading_requirements_from_cli():
    c = Config()
    opts = {
        'specifiers': ['other_package'],
        'requirements': ['requirements.txt'],
        'editables': ['.'],
        'output': None,
    }
    c.merge_cli_options(opts)
    assert c['pip2nix']['requirements'] == \
        ['other_package', '-e .', '-r requirements.txt']


def test_get_requirements():
    c = Config()
    c.merge_options({'pip2nix': {
        'requirements': ['simple', '-rreqs.txt', '-e editable']}})
    assert list(c.get_requirements()) == \
        [(None, 'simple'), ('-r', 'reqs.txt'), ('-e', 'editable')]


def test_get_package_config():
    c = Config()
    c.merge_options({
        'pip2nix:package:psycopg2': {
            'additional_requirements': ['nix:pkgs.postgresql']}})
    pkg_conf = c.get_package_config('psycopg2')
    assert pkg_conf == {'additional_requirements': ['nix:pkgs.postgresql']}


def test_finding_config_file(tmpdir, cwd):
    subdir = tmpdir.mkdir('sub')
    subdir.join('setup.cfg').write('[default]\na = sub/setup.cfg\n')
    subdir.join('pip2nix.ini').write('[default]\na = sub/pip2nix.ini\n')
    tmpdir.join('pip2nix.ini').write('[pip2nix]\na = ./pip2nix.ini\n')

    cwd(str(subdir))
    c = Config()
    c.find_and_load()

    assert c['pip2nix']['a'] == './pip2nix.ini'
