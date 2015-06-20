from setuptools import setup
import sys


setup(
    name="pip2nix",
    install_requires=["pip>=7"],
    tests_require=['pytest'],
    packages=['pip2nix'],
    entry_points={
        "console_scripts": [
            "pip2nix=pip2nix:main",
            "pip2nix%s=pip2nix:main" % sys.version[:1],
            "pip2nix%s=pip2nix:main" % sys.version[:3],
        ],
        "egg_info.writers": [
            "tests_require.txt=pip2nix.egg_writer:write_arg"
        ]
    }
)
