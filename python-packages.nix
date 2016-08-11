{
  MarkupSafe = super.buildPythonPackage {
    name = "MarkupSafe-0.23";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/M/MarkupSafe/MarkupSafe-0.23.tar.gz";
      md5 = "f5ab3deee4c37cd6a922fb81e730da6e";
    };
  };
  click = super.buildPythonPackage {
    name = "click-6.3";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/c/click/click-6.3.tar.gz";
      md5 = "2f171cdf12b8f2e284c224825f5e4634";
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
  jinja2 = super.buildPythonPackage {
    name = "jinja2-2.8";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [MarkupSafe];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.8.tar.gz";
      md5 = "edb51693fe22c53cee5403775c71a99e";
    };
  };
  pip = super.buildPythonPackage {
    name = "pip-8.1.1";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pip/pip-8.1.1.tar.gz";
      md5 = "6b86f11841e89c8241d689956ba99ed7";
    };
  };
  pip2nix = super.buildPythonPackage {
    name = "pip2nix-0.2.0.dev1";
    buildInputs = with self; [pytest];
    doCheck = true;
    makeWrapperArgs = "--prefix PATH : ${pkgs.nix-prefetch-scripts}";
    propagatedBuildInputs = with self; [pip configobj click contexter jinja2];
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
    name = "pytest-2.9.1";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [py];
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pytest/pytest-2.9.1.tar.gz";
      md5 = "05165740ea50928e4e971378630163ec";
    };
  };
}
