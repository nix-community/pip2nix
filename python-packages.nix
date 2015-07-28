{
  pip = self.buildPythonPackage {
    name = "pip-7.1.0";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-7.1.0.tar.gz";
      md5 = "d935ee9146074b1d3f26c5f0acfd120e";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };
  configobj = self.buildPythonPackage {
    name = "configobj-5.0.6";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/c/configobj/configobj-5.0.6.tar.gz";
      md5 = "e472a3a1c2a67bb0ec9b5d54c13a47d6";
    };
    propagatedBuildInputs = with self; [six];
    buildInputs = with self; [];
    doCheck = false;
  };
  pip2nix = self.buildPythonPackage {
    name = "pip2nix-0.1.dev1";
    src = ./.;
    propagatedBuildInputs = with self; [pip configobj];
    makeWrapperArgs = "--prefix PATH : ${pkgs.nix-prefetch-scripts}";
    buildInputs = with self; [pytest];
    doCheck = true;
  };
  six = self.buildPythonPackage {
    name = "six-1.9.0";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/s/six/six-1.9.0.tar.gz";
      md5 = "476881ef4012262dfc8adc645ee786c4";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };

### Test requirements

  py = self.buildPythonPackage {
    name = "py-1.4.30";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/py/py-1.4.30.tar.gz";
      md5 = "a904aabfe4765cb754f2db84ec7bb03a";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };
  pytest = self.buildPythonPackage {
    name = "pytest-2.7.2";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pytest/pytest-2.7.2.tar.gz";
      md5 = "dcd8e891474d605b81fc7fcc8711e95b";
    };
    propagatedBuildInputs = with self; [py];
    buildInputs = with self; [];
    doCheck = false;
  };
}
