{ pkgs ? import <nixpkgs> {}
, sphinxPackages
, sourceDateEpoch
}:

with pkgs.lib;

let

  pip2nix-src = (import ./default.nix { inherit pkgs; }).pip2nix.src;

  # Sphinx renders the year of SOURCE_DATE_EPOCH as the copyright year,
  # so the last commit's date advances it on its own.
  SOURCE_DATE_EPOCH = toString sourceDateEpoch;

  # stdenv defaults the epoch to 1980, which renders as the copyright
  # year without failing. Not `preBuild`: a `buildPhase` attribute
  # replaces the function that runs the hooks.
  refuse-a-placeholder-epoch = ''
    year=$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y)
    if [ "$year" -lt 2015 ]; then
      echo "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH renders the copyright year as $year" >&2
      exit 1
    fi
  '';

  make-pip2nix = {pythonVersion}: {
    name = "python${pythonVersion}";
    value = (import ./default.nix {
      inherit pkgs;
      pythonPackages = "python${pythonVersion}Packages";
    }).pip2nix;
  };

  jobs = rec {

    pip2nix = filterAttrs (n: v: n != "recurseForDerivations") (
      pkgs.lib.recurseIntoAttrs (
        builtins.listToAttrs (map make-pip2nix ([]
        ++ optional (hasAttr "python311Packages" pkgs) {pythonVersion = "311";}
        ++ optional (hasAttr "python312Packages" pkgs) {pythonVersion = "312";}
        ++ optional (hasAttr "python313Packages" pkgs) {pythonVersion = "313";}
        ++ optional (hasAttr "python314Packages" pkgs) {pythonVersion = "314";}
        ))
      )
    );

    docs = pkgs.stdenv.mkDerivation {
      name = "pip2nix-docs";
      src = pip2nix-src;
      inherit SOURCE_DATE_EPOCH;
      # Not full-sphinx-env, which carries the texlive only the PDF needs.
      nativeBuildInputs = [
        sphinxPackages.sphinx-env
      ];
      buildPhase = ''
        ${refuse-a-placeholder-epoch}
        cd docs
        sphinx-build -M html . _build
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

    docs-pdf = pkgs.stdenv.mkDerivation {
      name = "pip2nix-docs-pdf";
      src = pip2nix-src;
      inherit SOURCE_DATE_EPOCH;
      nativeBuildInputs = [
        sphinxPackages.full-sphinx-env
      ];
      buildPhase = ''
        ${refuse-a-placeholder-epoch}
        cd docs
        # texlive generates fonts below $HOME, which the sandbox points
        # at a directory nothing may write to.
        export HOME="$TMPDIR"
        sphinx-build -M latexpdf . _build
      '';
      installPhase = ''
        mkdir $out
        cp _build/latex/*.pdf $out

        # Hydra integration
        mkdir -p $out/nix-support
        for f in $out/*.pdf; do
          echo "doc manual $f" >> "$out/nix-support/hydra-build-products"
        done
      '';
    };

  };

in jobs
