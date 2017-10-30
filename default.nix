{ pkgs ? (import <nixpkgs> {})
, pythonPackages ? "python36Packages"
}:

with pkgs.lib;
let
  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  # Works with the new python-packages, still can fallback to the old
  # variant.
  basePythonPackagesUnfix = basePythonPackages.__unfix__ or (
    self: basePythonPackages.override (a: { inherit self; }));

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
    pip2nix = super.pip2nix.override (attrs: {
      src = pip2nix-src;
      buildInputs = [
        self.pip
        pkgs.nix
      ] ++ attrs.buildInputs;
      preBuild = ''
        export NIX_PATH=nixpkgs=${pkgs.path}
        export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
      '';
    });
    pip = basePythonPackages.pip;
  };

  pythonPackagesGenerated = import ./python-packages.nix {
    inherit pkgs;
    inherit (pkgs) fetchurl fetchgit;
  };

  myPythonPackages =
    (fix
    (extends pythonPackagesLocalOverrides
    (extends pythonPackagesGenerated
             basePythonPackagesUnfix)));

in myPythonPackages.pip2nix
