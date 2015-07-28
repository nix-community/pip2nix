pip2nix
=======

Generate nix expressions for Python packages.

.. image:: https://drone.io/github.com/ktosiek/pip2nix/status.png
   :target: https://drone.io/github.com/ktosiek/pip2nix/latest
   :alt: Build Status


.. image:: https://readthedocs.org/projects/pip2nix/badge/?version=latest
   :target: http://pip2nix.readthedocs.org/en/latest/
   :alt: Documentation Status

Why another .nix generator for Python?
======================================

I needed something that can work not only with pypi but also with local paths, VCS links, and dependency links.
I couldn't get any of the other generators to work, so I started my own :-)

Installation
============

::

    $ git clone htts://github.com/ktosiek/pip2nix
    $ nix-env -f pip2nix/release.nix -iA pip2nix.python34  # Same Python as target packages

Usage
=====

To generate python-packages.nix for a set of requirements::

    $ pip2nix -r requirements.txt

``pip2nix`` takes the same set of package specifications ``pip install`` does.

At the moment the --help lies - it's not only showing the ``pip2nix`` options, but also ``pip`` ones (that are not always relevant). (TODO: `#14 <https://github.com/ktosiek/pip2nix/issues/14>`_)

Contact
=======

Problems and questions should go to GitHub `issues <https://github.com/ktosiek/pip2nix/issues>`_.
If you need real-time help you can try pinging me - I'm ktosiek on Freenode, and `@tkontusz <https://twitter.com/tkontusz>`_ on Twitter.
