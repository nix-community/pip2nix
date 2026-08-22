import os
import subprocess

import pytest


# Long enough that a registry which does answer is not cut off, short
# enough that one which does not costs a wait rather than an evening.
NIXPKGS_TIMEOUT_SECONDS = 30

# The developer's own settings would otherwise reach the fixture, and
# commit or tag signing makes it fail.
ISOLATED_FROM_USER_CONFIG = dict(
    os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull
)

DEVSHELL_HINT = (
    "`<nixpkgs>` does not resolve. Run the suite through `just "
    "test-integration`, which enters the devShell that sets NIX_PATH."
)


@pytest.fixture(scope="session", autouse=True)
def resolvable_nixpkgs():
    """
    `<nixpkgs>` answering from the search path rather than from a fetch.

    Three tests reach it -- the license lookup, the profile build and the
    scaffolded `default.nix` -- and none of them passes nix a timeout, so
    an unanswered `<nixpkgs>` is a wait of minutes at every call instead
    of one failure here.
    """
    try:
        subprocess.run(
            ["nix-instantiate", "--eval", "--expr", "<nixpkgs>"],
            capture_output=True,
            check=True,
            text=True,
            timeout=NIXPKGS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"{DEVSHELL_HINT} It did not answer within {NIXPKGS_TIMEOUT_SECONDS}s."
        )
    except subprocess.CalledProcessError as error:
        pytest.fail(f"{DEVSHELL_HINT} nix said: {error.stderr.strip()}")


@pytest.fixture
def remote(tmp_path):
    """
    A repository whose `feature` branch is behind the default branch.

    That is what makes the tests discriminating: fetching the default
    branch head was the old behaviour, so a commit that is also that
    head would let the bug pass unnoticed.
    """
    git(tmp_path, "init", "--initial-branch", "main", "--quiet")
    git(tmp_path, "config", "user.email", "stub-user@corp.example")
    git(tmp_path, "config", "user.name", "stub-user")
    git(tmp_path, "commit", "--allow-empty", "--quiet", "-m", "Initial commit")
    git(tmp_path, "branch", "feature")
    git(tmp_path, "commit", "--allow-empty", "--quiet", "-m", "Second commit")

    return Remote(tmp_path)


class Remote:
    def __init__(self, path):
        self.url = f"file://{path}"
        self.path = path

    def sha(self, ref):
        return git(self.path, "rev-parse", ref)


def git(cwd, *args):
    return (
        subprocess.check_output(
            ["git"] + list(args), cwd=str(cwd), env=ISOLATED_FROM_USER_CONFIG
        )
        .decode()
        .strip()
    )
