#!/usr/bin/env bash
set -e

FORCE_REBUILD=

show_help() {
    echo "./bootstrap.sh [--force]"
    echo "  --force  Recreate the virtualenv even if it looks fresh"
}

while [ -n "$1" ]; do
    case "$1" in
        --help) show_help; exit 0;;
        --force) FORCE_REBUILD=1;;
        *)
            echo "Unknown option $1"
            echo
            show_help
            exit 1
            ;;
    esac
    shift
done

NIXPKGS="${NIXPKGS:-nixpkgs-20.09}"
PYTHON="${PYTHON:-python39}"
PIP=$(nix eval --impure --expr "(import ./nix { nixpkgs = (import ./nix/sources.nix).\"$NIXPKGS\"; }).${PYTHON}Packages.pip.version")
PIP=${PIP//\"/}

if [ "$FORCE_REBUILD" -o \
     ! -f ./_bootstrap_env/.done \
     -o ./_bootstrap_env/.done -ot setup.py ]; then

    VIRTUALENV=$(type -p virtualenv || true)
    if [ ! "$VIRTUALENV" ]; then
        echo -e '\e[1m`virtualenv` not found, restarting self in a nix-shell\e[0m'
        exec nix-shell -p "(import ./nix { nixpkgs = (import ./nix/sources.nix).\"$NIXPKGS\"; }).${PYTHON}Packages.virtualenv" --run "$0 $@ --force"
    fi

    $VIRTUALENV ./_bootstrap_env
    ./_bootstrap_env/bin/pip install -e ./ pip==$PIP
    touch ./_bootstrap_env/.done
fi

./_bootstrap_env/bin/pip2nix generate --licenses --no-binary :all:
