{
  pip = self.buildPythonPackage {
    doCheck = false;
    name = "pip-7.0.3";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-7.0.3.tar.gz";
      md5 = "54cbf5ae000fb3af3367345f5d299d1c";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
  };
  pip2nix = self.buildPythonPackage {
    doCheck = true;
    name = "pip2nix-0.0.0";
    src = ./.;
    propagatedBuildInputs = with self; [pip];
    buildInputs = with self; [pytest];
  };

### Test requirements

  pytest = self.buildPythonPackage {
    doCheck = false;
    name = "pytest-2.7.1";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pytest/pytest-2.7.1.tar.gz";
      md5 = "e972d691ff6779ffb4b594449bac3e43";
    };
    propagatedBuildInputs = with self; [py];
    buildInputs = with self; [];
  };
  py = self.buildPythonPackage {
    doCheck = false;
    name = "py-1.4.28";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/py/py-1.4.28.tar.gz";
      md5 = "30b807e1fe1b886578c47337d424a083";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
  };
}
