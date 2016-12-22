{ pkgs ? (import <nixpkgs> {}) }:
with pkgs.lib; rec {
  make-pip2nix = {pythonVersion}: {
    name = "python${pythonVersion}";
    value = import ./default.nix {
      inherit pkgs;
      pythonPackages = "python${pythonVersion}Packages";
    };
  };

  pip2nix = pkgs.recurseIntoAttrs (
    builtins.listToAttrs (map make-pip2nix ([
      {pythonVersion = "27";}
      {pythonVersion = "33";}
      {pythonVersion = "34";}
      {pythonVersion = "35";}
    ] ++ optional (hasAttr "python36Packages" pkgs) {pythonVersion = "36";}))
  );

  docs = pkgs.stdenv.mkDerivation {
    name = "pip2nix-docs";
    src = ./docs;
    #outputs = [ "html" ];  # TODO: PDF would be even nicer on CI
    buildInputs = [ pip2nix.python35 ] ++ (with  pkgs.python35Packages; [
      sphinx
    ]);
    buildPhase = ''make html'';
    installPhase = "cp -r _build/html $out";
  };
}
