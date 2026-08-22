import subprocess
import sys
from textwrap import dedent


INFRASTRUCTURE = ("pip2nix.prefetch", "pip2nix.license_lookup")


def test_the_renderer_imports_no_infrastructure():
    """
    The composition root hands the renderer what resolves a hash and a
    license attribute, so an import creeping back in is what turns that
    parameter into a dependency again.
    """
    check = dedent(f"""\
        import sys
        import pip2nix.models.license
        import pip2nix.output
        reached = [name for name in {INFRASTRUCTURE!r} if name in sys.modules]
        assert not reached, reached
        """)

    subprocess.check_call([sys.executable, "-c", check])
