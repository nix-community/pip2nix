import subprocess
import sys
from textwrap import dedent


def test_the_report_path_imports_without_pips_internals():
    """
    ADR-0001 rests on the report path being free of `pip._internal`, and an
    import that creeps back in is invisible until pip is gone.
    """
    check = dedent("""\
        import sys
        import pip2nix.cli
        import pip2nix.output
        import pip2nix.report
        import pip2nix.resolver
        internals = [name for name in sys.modules if name.startswith('pip._')]
        assert not internals, internals
        """)

    subprocess.check_call([sys.executable, "-c", check])
