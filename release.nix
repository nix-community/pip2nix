{ pkgs ? import ./nix { nixpkgs = builtins.getAttr nixpkgs sources; }
, sources ? import ./nix/sources.nix
, nixpkgs ? "nixpkgs-20.09"
}:

with pkgs.lib;

let

  make-pip2nix = {pythonVersion}: {
    name = "python${pythonVersion}";
    value = import ./default.nix {
      inherit pkgs;
      pythonPackages = "python${pythonVersion}Packages";
    };
  };

  jobs = rec {

    pip2nix = filterAttrs (n: v: n != "recurseForDerivations") (
      pkgs.recurseIntoAttrs (
        builtins.listToAttrs (map make-pip2nix ([]
        ++ optional (hasAttr "python27Packages" pkgs) {pythonVersion = "27";}
        ++ optional (hasAttr "python33Packages" pkgs) {pythonVersion = "33";}
        ++ optional (hasAttr "python34Packages" pkgs) {pythonVersion = "34";}
        ++ optional (hasAttr "python35Packages" pkgs) {pythonVersion = "35";}
        ++ optional (hasAttr "python36Packages" pkgs) {pythonVersion = "36";}
        ++ optional (hasAttr "python37Packages" pkgs) {pythonVersion = "37";}
        ++ optional (hasAttr "python38Packages" pkgs) {pythonVersion = "38";}
        ++ optional (hasAttr "python39Packages" pkgs) {pythonVersion = "39";}
        ++ optional (hasAttr "python310Packages" pkgs) {pythonVersion = "310";}
        ))
      )
    );

    docs = pkgs.stdenv.mkDerivation {
      name = "pip2nix-docs";
      src = pip2nix.python36.src;
      #outputs = [ "html" ];  # TODO: PDF would be even nicer on CI
      buildInputs = [ pip2nix.python36 ] ++ (with  pkgs.python36Packages; [
        sphinx
      ]);
      buildPhase = ''
        cd docs
        make html
      '';
      installPhase = ''
        mkdir $out
        cp -r _build/html $out

        # Hydra integration
        mkdir -p $out/nix-support
        echo "doc manual $out/html index.html" >> \
          "$out/nix-support/hydra-build-products"
      '';
    };

  };

in jobs
