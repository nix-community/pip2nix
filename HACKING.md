# Development environment

Just running `nix-shell` when in the repository should drop you into a shell with python2.7 and pip2nix wrapper in $PATH.
To use a different python, pass `--argstr pythonPackages python34Packages` to `nix-shell`.

# Running tests

To run tests while in the development environment run `py.test`. It will search for all tests under current directory.
To test all supported platforms, run `nix-build ./release.nix` - this is actually what CI does.
