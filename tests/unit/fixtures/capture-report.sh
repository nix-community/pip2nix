#!/usr/bin/env bash
#
# Capture an installation report as a test fixture.
#
# The fixtures are pip's output as written, not a selection from it. An
# earlier version kept only the fields pip2nix reads, which is how the
# licence metadata the report does carry stayed invisible for two
# sprints. pip writes the JSON sorted and indented, so the whole report
# reviews and diffs perfectly well.
#
# Re-run this to refresh one against a newer pip:
#
#   ./capture-report.sh report-git.json \
#       'six @ git+https://github.com/benjaminp/six@1.16.0'
#
# Nothing is pinned on purpose: the capture uses whichever pip nixpkgs
# currently provides, which is what makes re-running it worthwhile.
# Needs network, and the resolution has to be reproducible -- pin every
# requirement to an exact version or commit, or the refreshed fixture
# will not match what the tests assert.
#
# A report records the index it resolved against, so read a capture
# before committing it if it came from anywhere but a public index.
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "usage: $0 <fixture.json> <requirement>..." >&2
    exit 2
fi

fixture="$1"
shift

fixtures_dir="$(dirname "$(readlink -f "$0")")"

nix shell nixpkgs#python3Packages.pip --command \
    pip install --dry-run --ignore-installed --quiet \
        --report "$fixtures_dir/$fixture" "$@"

echo "Wrote $fixtures_dir/$fixture" >&2
