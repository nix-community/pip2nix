========
Glossary
========

The words pip2nix uses for the things it names, where a looser word
would leave a value's width unstated.

.. glossary::
   :sorted:

   Commit ID
      A git object name: the forty hexadecimal characters identifying
      one commit. pip's installation report carries it as
      ``commit_id``, and it is what a generated ``fetchgit`` source is
      pinned to.

   Revision
      Anything git resolves to an object -- a branch name, a tag, a
      :term:`commit ID`. The wide word, for a value that may be any of
      them, and what a run reports when it cannot resolve one.

   Reference
      A named pointer under ``refs/``, such as ``refs/heads/main``.
      Every reference is a :term:`revision`; not every revision is a
      reference.

   Rev
      Nix's attribute name on ``fetchgit``, which accepts a
      :term:`revision`. pip2nix writes a :term:`commit ID` into it and
      uses the spelling nowhere else. See :ref:`ADR-0013 <adr-0013>`.
