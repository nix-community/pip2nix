"""
The pyproject.toml constructs that broke generation must parse.

Both shapes below come from real packages and are what pip 20.1.1's
vendored `toml` 0.10 chokes on: every 0.10.x release implements TOML
0.5 and rejects constructs TOML 1.0 permits. `models/package.py` reads
`pyproject.toml` with stdlib `tomllib` instead, so these are the
acceptance check for that -- and for any replacement parser.

The counterpart tests that asserted `toml`'s broken behaviour are gone
along with the dependency. The library was abandoned at 0.10.2 in 2020,
and keeping it installed only to characterise it is not worth it; pip
itself moved to `tomli`.
"""

import tomllib


# MarkupSafe 3.x uses this shape in [tool.tox.env_run_base]. It is why
# nix-tryton has to pin MarkupSafe < 3 -- 2.1.x ships no pyproject.toml
# at all, so nothing gets parsed.
NESTED_ARRAY_WITH_INLINE_TABLE = """\
commands = [[
    "pytest",
    {replace = "posargs", default = [], extend = true},
]]
"""

HETEROGENEOUS_ARRAY = 'commands = ["pytest", {replace = "posargs"}]\n'


def test_nested_array_with_inline_table_is_valid_toml():
    parsed = tomllib.loads(NESTED_ARRAY_WITH_INLINE_TABLE)

    assert parsed["commands"] == [
        ["pytest", {"replace": "posargs", "default": [], "extend": True}]
    ]


def test_heterogeneous_array_is_valid_toml():
    parsed = tomllib.loads(HETEROGENEOUS_ARRAY)

    assert parsed["commands"] == ["pytest", {"replace": "posargs"}]
