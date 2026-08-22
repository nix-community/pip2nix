Correct what the design chapter claims a green build proves. A
``wheel`` or ``pyproject`` package is checked against its own metadata
while it builds and a ``setuptools`` package is not, where the chapter
described a single uniform guarantee. It also named
``nativeCheckInputs`` as what turns the check phase on, which needs a
check hook as well.
