{
  pip2nix = self.buildPythonPackage {
    doCheck = false;
    name = "pip2nix-0.0.0";
    src = ./.;
    propagatedBuildInputs = with self; [pip];
  };
  pip = self.buildPythonPackage {
    doCheck = false;
    name = "pip-7.0.3";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-7.0.3.tar.gz";
      md5 = "54cbf5ae000fb3af3367345f5d299d1c";
    };
    propagatedBuildInputs = with self; [];
  };
}
