from os import path
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
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), 'rb') as f:
    long_description = f.read().decode('utf-8')

VERSION = '0.6.0'

setup(
    name="pip2nix",
    version=VERSION,
    description='Generate Nix expressions for Python packages.',
    long_description=long_description,
    url="https://github.com/johbo/pip2nix",
    author="Tomasz Kontusz",
    author_email="tomasz.kontusz@gmail.com",
    license='GPLv3+',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='nix pip',

    install_requires=[
        'pip>=8,<10',
        'configobj>=5',
        'click',
        'contexter',
        'jinja2',
    ],
    tests_require=['pytest'],
    packages=['pip2nix', 'pip2nix.models'],
    package_data={'pip2nix': ['*.ini', '*.j2']},
    cmdclass={'test': PyTest},
    entry_points={
        "console_scripts": [
            "pip2nix=pip2nix.cli:cli",
            "pip2nix%s=pip2nix.cli:cli" % sys.version[:1],
            "pip2nix%s=pip2nix.cli:cli" % sys.version[:3],
        ],
        "egg_info.writers": [
            "tests_require.txt=pip2nix.egg_writer:write_arg"
        ]
    }
)
