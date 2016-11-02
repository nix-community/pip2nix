{
  MarkupSafe = super.buildPythonPackage {
    name = "MarkupSafe-0.23";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/c0/41/bae1254e0396c0cc8cf1751cb7d9afc90a602353695af5952530482c963f/MarkupSafe-0.23.tar.gz";
      md5 = "f5ab3deee4c37cd6a922fb81e730da6e";
    };
  };
  click = super.buildPythonPackage {
    name = "click-6.6";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/7a/00/c14926d8232b36b08218067bcd5853caefb4737cda3f0a47437151344792/click-6.6.tar.gz";
      md5 = "d0b09582123605220ad6977175f3e51d";
    };
  };
  configobj = super.buildPythonPackage {
    name = "configobj-5.0.6";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [six];
    src = fetchurl {
      url = "https://pypi.python.org/packages/64/61/079eb60459c44929e684fa7d9e2fdca403f67d64dd9dbac27296be2e0fab/configobj-5.0.6.tar.gz";
      md5 = "e472a3a1c2a67bb0ec9b5d54c13a47d6";
    };
  };
  contexter = super.buildPythonPackage {
    name = "contexter-0.1.3";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/f4/a4/a42a6401bfe2a05fe63e328a8e1b37881e4c286a8029fec1577949d6a8b5/contexter-0.1.3.tar.gz";
      md5 = "437efd28f5489cccfe929c08c6b269aa";
    };
  };
  jinja2 = super.buildPythonPackage {
    name = "jinja2-2.8";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [MarkupSafe];
    src = fetchurl {
      url = "https://pypi.python.org/packages/f2/2f/0b98b06a345a761bec91a079ccae392d282690c2d8272e708f4d10829e22/Jinja2-2.8.tar.gz";
      md5 = "edb51693fe22c53cee5403775c71a99e";
    };
  };
  pip = super.buildPythonPackage {
    name = "pip-8.1.2";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [];
    src = fetchurl {
      url = "https://pypi.python.org/packages/e7/a8/7556133689add8d1a54c0b14aeff0acb03c64707ce100ecd53934da1aa13/pip-8.1.2.tar.gz";
      md5 = "87083c0b9867963b29f7aba3613e8f4a";
    };
  };
  pip2nix = super.buildPythonPackage {
    name = "pip2nix-0.4.0";
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
      url = "https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz";
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
      url = "https://pypi.python.org/packages/f4/9a/8dfda23f36600dd701c6722316ba8a3ab4b990261f83e7d3ffc6dfedf7ef/py-1.4.31.tar.gz";
      md5 = "5d2c63c56dc3f2115ec35c066ecd582b";
    };
  };
  pytest = super.buildPythonPackage {
    name = "pytest-3.0.2";
    buildInputs = with self; [];
    doCheck = false;
    propagatedBuildInputs = with self; [py];
    src = fetchurl {
      url = "https://pypi.python.org/packages/2b/05/e20806c99afaff43331f5fd8770bb346145303882f98ef3275fa1dd66f6d/pytest-3.0.2.tar.gz";
      md5 = "61dc36e65a6f6c11c53b1388e043a9f5";
    };
  };
}
