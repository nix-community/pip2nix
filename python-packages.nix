{
  pip = self.buildPythonPackage {
    doCheck = false;
    name = "pip-7.1.0";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-7.1.0.tar.gz";
      md5 = "d935ee9146074b1d3f26c5f0acfd120e";
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
    name = "pytest-2.7.2";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pytest/pytest-2.7.2.tar.gz";
      md5 = "dcd8e891474d605b81fc7fcc8711e95b";
    };
    propagatedBuildInputs = with self; [py];
    buildInputs = with self; [];
  };
  py = self.buildPythonPackage {
    doCheck = false;
    name = "py-1.4.30";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/py/py-1.4.30.tar.gz";
      md5 = "a904aabfe4765cb754f2db84ec7bb03a";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
  };
}
