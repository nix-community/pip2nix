#!/usr/bin/env bash
#
# Re-generate every captured report fixture, so that each one has its
# requirement written down rather than remembered.
#
# `report-single-wheel.json` is deliberately absent: it is written by
# hand around an `.example` index url rather than captured.
#
# Refreshing against a newer pip can move the versions it resolves, so
# expect to update what the tests assert along with the fixtures.
set -euo pipefail

here="$(dirname "$(readlink -f "$0")")"

"$here/capture-report.sh" report-git.json \
    'six @ git+https://github.com/benjaminp/six@1.16.0'

"$here/capture-report.sh" report-trytond-account.json \
    'trytond_account == 7.0.28'

# The pair behind the sdist substitution of ADR-0003: what pip resolves
# on its own, and what it resolves once the wheel is refused. Both have
# to name the same version, or there is nothing to swap.
"$here/capture-report.sh" report-binary-wheel.json \
    'asyncpg == 0.30.0'

"$here/capture-report.sh" report-binary-wheel-sdist.json \
    --no-binary asyncpg 'asyncpg == 0.30.0'

# A package that declares setuptools at runtime, which is what
# `excluded_packages` keeps out of the emitted set and out of the edge
# naming it. setuptools itself stays unpinned on purpose: nothing
# asserts its version, so a refresh may move it freely.
"$here/capture-report.sh" report-setuptools.json \
    'zc.lockfile == 3.0.post1'
