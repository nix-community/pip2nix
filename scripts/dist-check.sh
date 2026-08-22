#!/usr/bin/env bash
#
# Install what `just dist` built and generate with it, which is what
# proves an artifact carries a working pip2nix rather than only metadata
# that reads well. The last pass installs into a virtualenv that carries
# no pip of its own -- the environment `uv` and `pipx` create, and the
# one that catches an undeclared dependency on the resolver.
#
# Resolves against PyPI, and prefetches what it resolves into the store.

set -euo pipefail
shopt -s nullglob

wheels=(dist/*.whl)
sdists=(dist/*.tar.gz)
if [ ${#wheels[@]} -ne 1 ] || [ ${#sdists[@]} -ne 1 ]; then
    echo "dist-check: dist/ carries ${#wheels[@]} wheels and" \
         "${#sdists[@]} sdists, expected one of each --" \
         "run just clean and just dist" >&2
    exit 1
fi

# An artifact left from an earlier version installs and runs, so
# without this the check reports whatever that version got wrong.
version=$(sed -n -E 's/^version = "(.*)"/\1/p' pyproject.toml)
for artifact in "${wheels[0]}" "${sdists[0]}"; do
    case "$artifact" in
        *"-$version"[-.]*) ;;
        *)
            echo "dist-check: $artifact is not version $version --" \
                 "run just clean and just dist" >&2
            exit 1
            ;;
    esac
done

root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT

# A generation small enough to be quick and complete enough to reach
# every part of the program: it resolves, prefetches into the store and
# renders. `click` is a `-any` wheel, so no source distribution pass and
# no git repository are involved.
generate() {
    local venv="$1" project="$root/project"
    rm -rf "$project"
    mkdir "$project"
    echo click > "$project/requirements.txt"
    (cd "$project" && "$venv/bin/pip2nix" generate -r requirements.txt)
    grep -q '"click" = ' "$project/python-packages.nix"
}

for artifact in "${wheels[0]}" "${sdists[0]}"; do
    echo "==> $artifact, into a virtualenv that carries pip"
    python3 -m venv "$root/with-pip"
    "$root/with-pip/bin/pip" install --quiet "$artifact"
    generate "$root/with-pip"
    rm -rf "$root/with-pip"
done

echo "==> ${wheels[0]}, into a virtualenv that carries none"
uv venv --quiet "$root/without-pip"
uv pip install --quiet --python "$root/without-pip/bin/python" "${wheels[0]}"
generate "$root/without-pip"
