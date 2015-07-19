import os
from pip.index import Link
from pip2nix.main import link_to_nix
import pytest


@pytest.yield_fixture
def cwd():
    old_cwd = os.getcwd()
    yield
    os.chdir(old_cwd)


class Test_link_to_nix:
    def test_file_link(self, cwd, tmpdir):
        os.chdir(str(tmpdir))
        assert link_to_nix(Link('file://{}'.format(tmpdir))) == './.'

    def test_http_link(self):
        link = Link(
            'https://pypi.python.org/packages/source/p/pip/pip-7.0.3.tar.gz'
            '#md5=e972d691ff6779ffb4b594449bac3e43')
        assert link_to_nix(link) == (
            'fetchurl {\n'
            '  url = "https://pypi.python.org/packages/source/p/pip/pip-7.0.3.tar.gz";\n'
            '  md5 = "e972d691ff6779ffb4b594449bac3e43";\n'
            '}')
