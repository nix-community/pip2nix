import subprocess
import sys
from textwrap import dedent


INFRASTRUCTURE = ("pip2nix.prefetch", "pip2nix.license_lookup", "pip2nix.resolver")


def test_the_adapter_imports_no_infrastructure():
    """
    The composition root hands the adapter what runs pip and what puts a
    source into the store, so an import creeping back in is what turns
    that parameter into a dependency again.
    """
    check = dedent(f"""\
        import sys
        import pip2nix.report
        reached = [name for name in {INFRASTRUCTURE!r} if name in sys.modules]
        assert not reached, reached
        """)

    subprocess.check_call([sys.executable, "-c", check])
