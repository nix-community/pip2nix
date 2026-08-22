"""
The doubles are `mocker`, and `monkeypatch` is not a second way to write them.

pytest ships `monkeypatch` whether or not pytest-mock is installed, so the two
idioms stay available side by side and nothing but a guard keeps the suite on
one of them.
"""

from pathlib import Path


GUARD = Path(__file__)
TESTS = GUARD.parent.parent


def test_no_test_reaches_for_monkeypatch():
    users = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if path != GUARD and "monkeypatch" in path.read_text()
    )

    assert users == []
