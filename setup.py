from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name="pip2nix",
    install_requires=["pip>=7"],
    tests_require=['pytest'],
    packages=['pip2nix'],
    cmdclass={'test': PyTest},
    entry_points={
        "console_scripts": [
            "pip2nix=pip2nix.main:main",
            "pip2nix%s=pip2nix.main:main" % sys.version[:1],
            "pip2nix%s=pip2nix.main:main" % sys.version[:3],
        ],
        "egg_info.writers": [
            "tests_require.txt=pip2nix.egg_writer:write_arg"
        ]
    }
)
