
======
 Tips
======


Missing dependencies
====================

Some python packages depend on external libraries or applications to be
available already when running ``pip2nix generate``. The following example shows
a typical error:

.. code:: shell

    [nix-shell:~/wo/synapse]$ pip2nix generate -r requirements.txt -c constraints.txt

    Collecting pynacl==0.3.0 (from -r requirements.txt (line 47))
      Using cached PyNaCl-0.3.0.tar.gz
      Saved /var/folders/v2/kx2sg5693tb1h84zc2hmjjgr0000gn/T/tmpNYy5RApip2nix/PyNaCl-0.3.0.tar.gz
        Complete output from command python setup.py egg_info:
        Package libffi was not found in the pkg-config search path.
        Perhaps you should add the directory containing `libffi.pc'
        to the PKG_CONFIG_PATH environment variable

        [ ... ]

        ld: library not found for -lffi
        clang-4.0: error: linker command failed with exit code 1 (use -v to see invocation)
        Traceback (most recent call last):
          File "<string>", line 1, in <module>
          File "/private/var/folders/v2/kx2sg5693tb1h84zc2hmjjgr0000gn/T/pip-build-KcVPbJ/pynacl/setup.py", line 278, in <module>
            "Programming Language :: Python :: 3.4",
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/__init__.py", line 128, in setup
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/__init__.py", line 123, in _install_setup_requires
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/dist.py", line 455, in fetch_build_eggs
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/pkg_resources/__init__.py", line 866, in resolve
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/pkg_resources/__init__.py", line 1146, in best_match
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/pkg_resources/__init__.py", line 1158, in obtain
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/dist.py", line 522, in fetch_build_egg
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/command/easy_install.py", line 673, in easy_install
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/command/easy_install.py", line 699, in install_item
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/command/easy_install.py", line 882, in install_eggs
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/command/easy_install.py", line 1150, in build_and_install
          File "/nix/store/hlcj0hzxamapajgrbq3bkx1xlmfcx2f3-python2.7-setuptools-38.2.3/lib/python2.7/site-packages/setuptools-38.2.3-py2.7.egg/setuptools/command/easy_install.py", line 1138, in run_setup
        distutils.errors.DistutilsError: Setup script exited with error: command 'clang' failed with exit status 1

        ----------------------------------------
    Command "python setup.py egg_info" failed with error code 1 in /private/var/folders/v2/kx2sg5693tb1h84zc2hmjjgr0000gn/T/pip-build-KcVPbJ/pynacl/


This happens because `pip2nix` depends on the following call to find out about
some meta information of the package:

.. code:: shell

   python setup.py egg_info


Running the command inside of another invocation of `nix-shell` can usually
mitigate the trouble. As a one-shot command it looks as follows:

.. code:: shell

   nix-shell -p python27Packages.cffi \
          --command 'pip2nix generate -r requirements.txt -c constraints.txt'


Entering the sub shell needs a tweak to the environment variable `PATH` at the
moment. The next example shows how to run this in two steps:

.. code:: shell

   [nix-shell:~/wo/synapse]$ PATH=/bin:$PATH nix-shell -p python27Packages.cffi
   [nix-shell:~/wo/synapse]$ pip2nix generate -r requirements.txt -c constraints.txt
