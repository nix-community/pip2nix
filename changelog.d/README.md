# Changelog fragments

One file per change. A release collects them into a version section in
`CHANGELOG.rst` and removes them, so nothing here is edited by two
branches at once and a merge never conflicts over the changelog.

Name a fragment `<slug>.<type>.rst`, where the type is one of `added`,
`changed`, `deprecated`, `removed`, `fixed` or `security`. Prefix the
slug with `+` when there is no issue number behind it — without the
prefix, the part before the type is read as an issue reference.

```text
changelog.d/+reuse-store-for-git-sources.changed.rst
```

The content is the entry itself, written in reStructuredText for
someone consuming a release rather than reading the commits:

```rst
Stop cloning a repository the Nix store already holds
```

Write the entry without a leading `-`. towncrier adds the bullet when it
collects the fragments, so a dash here renders as `- - The entry`.

Order inside a section is towncrier's, not the order the fragments were
written. Entries carrying an issue reference come first, sorted by it;
`+` entries come last, sorted alphabetically by their own text. So the
entry you consider most important cannot be put at the top by naming
its file — write the section so that the order does not carry meaning.

**Do not delete this file.** A release removes every fragment it
consumed, git does not track an empty directory, and the next change
would then have nowhere to write.
