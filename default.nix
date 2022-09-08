{ pkgs ? (import <nixpkgs> {})
, pythonPackages ? "python3Packages"
}:

with pkgs.lib;
let
  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  elem = builtins.elem;
  basename = path: last (splitString "/" path);
  startsWith = prefix: full: let
    actualPrefix = builtins.substring 0 (builtins.stringLength prefix) full;
  in actualPrefix == prefix;

  src-filter = path: type:
    let
      ext = last (splitString "." path);
      parts = last (splitString "/" path);
    in
      !elem (basename path) [".git" "__pycache__" ".eggs" "_bootstrap_env"] &&
      !elem ext ["egg-info" "pyc"] &&
      !startsWith "result" (basename path);

  pip2nix-src = builtins.filterSource src-filter ./.;

  pythonPackagesLocalOverrides = self: super: {
    pip2nix = super.pip2nix.override (attrs: rec {
      src = pip2nix-src;
      buildInputs = [
        self.pip
        pkgs.nix
      ] ++ attrs.buildInputs;
      pythonWithSetuptools = self.python.withPackages(ps: with ps; [
        setuptools
      ]);
      propagatedBuildInputs = [
        pythonWithSetuptools
      ] ++ attrs.propagatedBuildInputs;
      preBuild = ''
        export NIX_PATH=nixpkgs=${pkgs.path}
        export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
      '';
      postInstall = ''
        for f in $out/bin/*
        do
          wrapProgram $f \
            --set PIP2NIX_PYTHON_EXECUTABLE ${pythonWithSetuptools}/bin/python
        done
      '';
    });

    pip = super.pip.override (attrs: rec {
      # pip detects that we already have bootstrapped_pip "installed", so we need
      # to force it a little.
      pipInstallFlags = [ "--ignore-installed" ];
    });
  };

  pythonPackagesGenerated = import ./python-packages.nix {
    inherit pkgs;
    inherit (pkgs) fetchurl fetchgit fetchhg;
  };

  # See
  # https://github.com/rihardsk/mautrix-hangouts-nix/commit/f5ed572b4b56b2daff002a860b5f4e00e175ed32
  myPythonPackages = let
    composedOverrides =
      (composeExtensions pythonPackagesGenerated pythonPackagesLocalOverrides);
    myPython = basePythonPackages.python.override { packageOverrides = composedOverrides; };
  in myPython.pkgs;

in myPythonPackages.pip2nix
