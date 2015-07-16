{ pkgs ? (import <nixpkgs> {}), pythonPackages ? "python27Packages" }:
let
  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  elem = builtins.elem;
  basename = path: with pkgs.lib; last (splitString "/" path);

  pip2nix-src = builtins.filterSource
    (path: type: !elem (basename path) [".git" "pip2nix.egg-info" "result"]) ./.;

  localOverrides = pythonPackages: {
    pip2nix = pythonPackages.pip2nix.override (pip2nix: {
      src = pip2nix-src;
      buildInputs = [pythonPackages.pip] ++ pip2nix.buildInputs;
    });
  };

  pythonPackagesWithLocals = basePythonPackages.override (a: {
    self = pythonPackagesWithLocals;
  })
  // (scopedImport {
    self = pythonPackagesWithLocals;
    inherit (pkgs) fetchurl;
  } ./python-packages.nix);

  myPythonPackages =
    pythonPackagesWithLocals
    // (localOverrides pythonPackagesWithLocals);
in myPythonPackages.pip2nix
