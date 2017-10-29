Installation
============

Using `pip2nix` directly out of the git repository can be achieved in the
following way::

  $ git clone https://github.com/johbo/pip2nix
  $ nix-env -f pip2nix/release.nix -iA pip2nix.python35

Instead of installing into the environment, another convenient way of using it
is based on `nix-shell`::

  $ nix-shell release.nix -A pip2nix.python36

Since `pip2nix` is not yet in a mature state, the usage of `nix-shell` is
recommended. It does allow to investigate problems on the spot, since it is
basically a development environment of `pip2nix`.


Basic usage
===========


Ad-hoc python-packages.nix generation
-------------------------------------

To generate python-packages.nix for a set of requirements::

    $ pip2nix generate -r requirements.txt

``pip2nix generate`` takes the same set of package specifications ``pip install`` does.
It understands ``-r``, git links, package specifications, and ``-e`` (which is just ignored).


Using pip2nix in a project
--------------------------

When packaging a project with pip2nix you'll want to make sure it's called the
same way every time you bump dependencies. To do that, you can create a
``pip2nix.ini`` file::

    [pip2nix]
    requirements = -r ./requirements.txt

This way you can just run ``pip2nix generate`` in the project's root.
More about the configuration file in :doc:`configuration`.

To actually use the generated packages file, you can create a default.nix with
``pip2nix scaffold``. To work on a project `myProject` you'd use::

    $ pip2nix scaffold --package myProject
    $ cat > pip2nix.ini <<EOF
    [pip2nix]
    requirements = .
    EOF
    $ pip2nix generate
    $ nix-shell  # all the deps should be available
