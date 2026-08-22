import io
import tarfile
import zipfile
from textwrap import dedent

from pip2nix.build_system import BuildSystem, read_build_system


ENVIRONMENT = {"sys_platform": "linux", "python_version": "3.13"}

PYPROJECT = dedent("""\
    [build-system]
    requires = ["setuptools", "wheel", "Cython >= 3"]
    build-backend = "setuptools.build_meta"
    """)


def write_pyproject(path, content=PYPROJECT):
    (path / "pyproject.toml").write_text(content)
    return str(path)


def write_tarball(path, members):
    with tarfile.open(path, "w:gz") as tar:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content.encode("utf-8")))
    return str(path)


def test_reads_the_requires_of_a_directory(tmp_path):
    path = write_pyproject(tmp_path)

    assert read_build_system(path, ENVIRONMENT).requires == [
        "setuptools",
        "wheel",
        "cython",
    ]


def test_reads_nothing_from_a_directory_without_a_pyproject(tmp_path):
    assert read_build_system(str(tmp_path), ENVIRONMENT) == BuildSystem()


def test_reads_nothing_from_a_pyproject_holding_only_tool_configuration(tmp_path):
    path = write_pyproject(
        tmp_path,
        dedent("""\
        [tool.black]
        line-length = 120
        """),
    )

    assert read_build_system(path, ENVIRONMENT) == BuildSystem()


def test_a_table_naming_no_requirements_still_declares_a_build_system(tmp_path):
    path = write_pyproject(
        tmp_path,
        dedent("""\
        [build-system]
        build-backend = "setuptools.build_meta"
        """),
    )

    assert read_build_system(path, ENVIRONMENT) == BuildSystem(declared=True)


def test_drops_a_requirement_whose_marker_does_not_hold(tmp_path):
    path = write_pyproject(
        tmp_path,
        dedent("""\
        [build-system]
        requires = ["tomli; python_version < '3.11'", "setuptools"]
        """),
    )

    assert read_build_system(path, ENVIRONMENT).requires == ["setuptools"]


def test_names_a_requirement_declared_twice_once(tmp_path):
    path = write_pyproject(
        tmp_path,
        dedent("""\
        [build-system]
        requires = ["Cython", "cython >= 3"]
        """),
    )

    assert read_build_system(path, ENVIRONMENT).requires == ["cython"]


def test_reads_the_requires_of_a_tarball(tmp_path):
    archive = write_tarball(
        tmp_path / "asyncpg-0.30.0.tar.gz", {"asyncpg-0.30.0/pyproject.toml": PYPROJECT}
    )

    assert read_build_system(archive, ENVIRONMENT).requires == [
        "setuptools",
        "wheel",
        "cython",
    ]


def test_reads_the_requires_of_a_zip(tmp_path):
    archive = tmp_path / "asyncpg-0.30.0.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("asyncpg-0.30.0/pyproject.toml", PYPROJECT)

    assert read_build_system(str(archive), ENVIRONMENT).requires == [
        "setuptools",
        "wheel",
        "cython",
    ]


def test_reads_nothing_from_an_archive_without_a_pyproject(tmp_path):
    archive = write_tarball(
        tmp_path / "polib-1.2.0.tar.gz", {"polib-1.2.0/setup.py": ""}
    )

    assert read_build_system(archive, ENVIRONMENT) == BuildSystem()
