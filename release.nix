{ pkgs ? (import <nixpkgs> {}) }:
rec {
  make-pip2nix = {pythonVersion}: {
    name = "python${pythonVersion}";
    value = import ./default.nix {
      inherit pkgs;
      pythonPackages = "python${pythonVersion}Packages";
    };
  };

  pip2nix = pkgs.recurseIntoAttrs (
    builtins.listToAttrs (map make-pip2nix [
      {pythonVersion = "27";}
      {pythonVersion = "33";}
      {pythonVersion = "34";}
    ])
  );
}
