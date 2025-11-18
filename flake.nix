{
  inputs = {
    nixpkgs = {
      type = "github";
      owner = "NixOS";
      repo = "nixpkgs";
      ref = "nixos-22.11";
    };

    flake-utils = {
      type = "github";
      owner = "numtide";
      repo = "flake-utils";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgsForSystem = import nixpkgs {
          inherit system;
        };
        releasePackages = import ./release.nix {
          pkgs = pkgsForSystem;
        };
        pythonPackages = import ./default.nix {
          pkgs = pkgsForSystem;
        };
      in
      {
        packages =
          (builtins.listToAttrs (
            builtins.map (subkey: {
              name = "pip2nix_${subkey}";
              value = releasePackages.pip2nix.${subkey};
            }) (builtins.attrNames releasePackages.pip2nix)
          ))
          // {
            docs = releasePackages.docs;
            default = releasePackages.pip2nix.python311;
          };

        devShells = {
          default = pkgsForSystem.mkShell {
            inputsFrom = [
              pythonPackages.pip2nix-for-shell
            ];
            packages = [
              pkgsForSystem.nix-prefetch-git
              pkgsForSystem.nix-prefetch-hg
            ];
          };
        };

      }
    );
}
