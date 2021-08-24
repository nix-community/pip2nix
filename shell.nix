{ pkgs ? (import <nixpkgs> {})
}:

pkgs.mkShell {
  buildInputs = [
    (import ./default.nix { inherit pkgs; })
    pkgs.nix-prefetch-git
    pkgs.nix-prefetch-hg
  ];
}
