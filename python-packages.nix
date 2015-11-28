{
  click = super.buildPythonPackage {
    name = "click-6.2";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/c/click/click-6.2.tar.gz";
      md5 = "83252a8095397b1f5f710fdd58b484d9";
    };
  };
  configobj = super.buildPythonPackage {
    name = "configobj-5.0.6";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [six];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/c/configobj/configobj-5.0.6.tar.gz";
      md5 = "e472a3a1c2a67bb0ec9b5d54c13a47d6";
    };
  };
  contexter = super.buildPythonPackage {
    name = "contexter-0.1.3";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/c/contexter/contexter-0.1.3.tar.gz";
      md5 = "437efd28f5489cccfe929c08c6b269aa";
    };
  };
  pip = super.buildPythonPackage {
    name = "pip-7.1.2";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-7.1.2.tar.gz";
      md5 = "3823d2343d9f3aaab21cf9c917710196";
    };
  };
  pip2nix = super.buildPythonPackage {
    name = "pip2nix-0.2.0.dev1";
    buildInputs = with self; [pytest];
    doCheck = true;
    makeWrapperArgs = "--prefix PATH : ${pkgs.nix-prefetch-scripts}";
    propagatedBuildInputs = with self; [pip configobj click contexter];
    src = ./.;
  };
  six = super.buildPythonPackage {
    name = "six-1.10.0";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz";
      md5 = "34eed507548117b2ab523ab14b2f8b55";
    };
  };

### Test requirements

  py = super.buildPythonPackage {
    name = "py-1.4.31";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/py/py-1.4.31.tar.gz";
      md5 = "5d2c63c56dc3f2115ec35c066ecd582b";
    };
  };
  pytest = super.buildPythonPackage {
    name = "pytest-2.8.3";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [py];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pytest/pytest-2.8.3.tar.gz";
      md5 = "33fd706c4ef857e70200661b0fceb80c";
    };
  };
}
