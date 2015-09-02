{ pkgs ? (import <nixpkgs> {}), pythonPackages ? "python27Packages" }:
let
  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  elem = builtins.elem;
  basename = path: with pkgs.lib; last (splitString "/" path);

  src-filter = path: type:
    with pkgs.lib;
    !elem (basename path) [".git" "pip2nix.egg-info" "_bootstrap_env" "result" "__pycache__" ".eggs"] &&
    (last (splitString "." path) != "pyc");

  pip2nix-src = builtins.filterSource src-filter ./.;

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
    super = basePythonPackages;
    inherit pkgs;
    inherit (pkgs) fetchurl;
  } ./python-packages.nix);

  myPythonPackages =
    pythonPackagesWithLocals
    // (localOverrides pythonPackagesWithLocals);
in myPythonPackages.pip2nix
