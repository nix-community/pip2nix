"""
Resolution, by running pip as a subprocess.

pip is asked for a `--report`, the documented and versioned JSON description
of what it would install. Nothing here touches `pip._internal`, which is the
point of ADR-0001.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass

from packaging.version import InvalidVersion, Version

from .config import Config
from .errors import ReportError


MINIMUM_PIP_VERSION = "22.2"


@dataclass(frozen=True)
class Resolver:
    """
    How pip is invoked: an interpreter, and the configuration its argument
    vector is built from.
    """

    python_executable: str
    config: Config

    def check_version(self):
        """
        Refuse a pip that cannot write an installation report.

        `--report` arrived in pip 22.2. An older one rejects the option as
        a usage error, which reads as if the requirements were the problem.
        """
        try:
            output = subprocess.check_output(
                [self.python_executable, "-m", "pip", "--version"]
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ReportError(
                f'Cannot run pip through "{self.python_executable}": {error}'
            )

        version = parse_pip_version(output.decode("utf-8"))
        if version < Version(MINIMUM_PIP_VERSION):
            raise ReportError(
                f"pip {version} cannot write an installation report, pip2nix "
                f"needs {MINIMUM_PIP_VERSION} or newer."
            )

    def resolve(self):
        return _read_report(self.argv())

    def resolve_source(self, package):
        return _read_report(self.source_argv(package))

    def argv(self):
        argv = self._argv()

        for constraint in self.config.constraints:
            argv += ["--constraint", constraint]

        for kind, requirement in self.config.get_requirements():
            if kind == "-r":
                argv += ["--requirement", requirement]
            elif kind == "-e":
                raise ReportError(
                    f'Editable requirements are not supported: "{requirement}". '
                    "The report describes them as a local directory, which loses "
                    "the url and the revision they were installed from."
                )
            else:
                argv.append(requirement)

        return argv

    def source_argv(self, package):
        """
        Refuse a wheel to this package alone.

        pip hands its format control on to the build environments it
        creates, so a second name here is a backend it would compile
        rather than install. That is what ADR-0005 exists to avoid.
        """
        return self._argv() + [
            "--no-deps",
            "--no-binary",
            package.name,
            f"{package.name}=={package.version}",
        ]

    def _argv(self):
        argv = [
            self.python_executable,
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--quiet",
        ]

        indexes = self.config.indexes
        if indexes:
            argv += ["--index-url", indexes[0]]
            for extra_index in indexes[1:]:
                argv += ["--extra-index-url", extra_index]
        else:
            argv.append("--no-index")

        return argv


def parse_pip_version(output):
    """
    The version out of what `pip --version` prints.

    That is one line, `pip 25.3 from /nix/store/... (python 3.13)`.
    """
    words = output.split()
    try:
        return Version(words[1])
    except (IndexError, InvalidVersion):
        raise ReportError(f'Cannot read a pip version from "{output.strip()}".')


def _read_report(argv):
    with tempfile.TemporaryDirectory(prefix="pip2nix-") as directory:
        report_path = os.path.join(directory, "report.json")
        try:
            subprocess.check_call(argv + ["--report", report_path])
        except subprocess.CalledProcessError as error:
            raise ReportError(
                "pip could not resolve the requirements, it exited with "
                f"status {error.returncode}."
            )
        with open(report_path) as report_file:
            return json.load(report_file)
