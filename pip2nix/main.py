from __future__ import unicode_literals

from contextlib import contextmanager
from collections import defaultdict
from copy import deepcopy
from subprocess import check_output
import sys

from .generate import NixFreezeCommand


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    cmd = NixFreezeCommand()

    return cmd.main(args)


if __name__ == '__main__':
    sys.exit(main())
