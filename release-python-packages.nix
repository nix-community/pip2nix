{
  pkginfo = self.buildPythonPackage {
    name = "pkginfo-1.2.1";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/p/pkginfo/pkginfo-1.2.1.tar.gz";
      md5 = "4489be0244c003744ca18758fa12e468";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };
  twine = self.buildPythonPackage {
    name = "twine-1.5.0";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/t/twine/twine-1.5.0.tar.gz";
      md5 = "12948245aeb59acf32f663e1d81fed34";
    };
    propagatedBuildInputs = with self; [pkginfo requests setuptools];
    buildInputs = with self; [];
    doCheck = false;
  };
  bumpversion = self.buildPythonPackage {
    name = "bumpversion-0.5.3";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/b/bumpversion/bumpversion-0.5.3.tar.gz";
      md5 = "c66a3492eafcf5ad4b024be9fca29820";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };
  requests = self.buildPythonPackage {
    name = "requests-2.7.0";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/r/requests/requests-2.7.0.tar.gz";
      md5 = "29b173fd5fa572ec0764d1fd7b527260";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };
  setuptools = super.buildPythonPackage {
    name = "setuptools-18.0.1";
    src = fetchurl {
      url = "https://pypi.python.org/packages/source/s/setuptools/setuptools-18.0.1.tar.gz";
      md5 = "cecd172c9ff7fd5f2e16b2fcc88bba51";
    };
    propagatedBuildInputs = with self; [];
    buildInputs = with self; [];
    doCheck = false;
  };

### Test requirements

  
}
