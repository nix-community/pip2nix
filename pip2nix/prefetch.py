"""
Putting a source into the Nix store, through the `nix-prefetch-*` tools.

Everything that reaches the store on a generation run lives here, so that
neither the renderer nor the report adapter has to carry a subprocess of
its own.
"""

import json
import logging
from subprocess import CalledProcessError, check_output

from .errors import ReportError


logger = logging.getLogger(__name__)


def prefetch_git(url, commit_id, expected_hash=None):
    argv = ["nix-prefetch-git", url, commit_id]
    if expected_hash:
        argv.append(expected_hash)
    else:
        logger.info("Prefetching %s at commit %s.", url, commit_id)
    out = _tool_output(argv, f"Cannot fetch {url} at commit {commit_id}")
    data = json.loads(out.decode("utf-8"))
    return data["sha256"], data["rev"] or commit_id, data["path"]


def prefetch_url_path(url, sha256):
    """
    Download `url` into the store and return where it landed.

    The hash the index published is what keeps this cheap: nix has the
    file after the first generation and does not fetch it again.
    """
    logger.info("Prefetching %s.", url)
    out = _tool_output(
        ["nix-prefetch-url", "--print-path", "--type", "sha256", url, sha256],
        f"Cannot fetch {url}",
    )
    return out.decode("utf-8").splitlines()[-1]


def _tool_output(argv, failure):
    """
    What a tool wrote, or a reported failure when it could not run.

    The tools are external to pip2nix, so a missing one and a refused
    fetch are both things a user can act on rather than defects.
    """
    try:
        return check_output(argv)
    except (OSError, CalledProcessError) as error:
        raise ReportError(f"{failure}: {error}.")
