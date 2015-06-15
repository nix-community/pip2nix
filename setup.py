from setuptools import setup
import sys


setup(
    name="pip2nix",
    install_requires=["pip>=7"],
    packages=['pip2nix'],
    entry_points={
        "console_scripts": [
            "pip2nix=pip2nix:main",
            "pip2nix%s=pip2nix:main" % sys.version[:1],
            "pip2nix%s=pip2nix:main" % sys.version[:3],
        ],
    }
)
