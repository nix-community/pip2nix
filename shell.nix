let
    pkgs = import <nixpkgs> {};
in
{ stdenv ? pkgs.stdenv
, pythonPackages ? pkgs.python27Packages }:

let
    pip = pkgs.lib.overrideDerivation pythonPackages.pip (a: {
        name = "pip-7.0.3";
        src = pkgs.fetchurl {
            url = "http://pypi.python.org/packages/source/p/pip/pip-7.0.3.tar.gz";
            md5 = "54cbf5ae000fb3af3367345f5d299d1c";
        };
        doCheck = false;
    });
in stdenv.mkDerivation {
    name = "virtualenv2nix";
    version = "0.1.0.0";
    src = ./.;
    buildInputs = with pythonPackages; [ ipython ipdb ] ++ [ pip ];
}
