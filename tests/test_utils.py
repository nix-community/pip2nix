from pip2nix import indent


def test_indenting_single_line():
    # First line is never indented
    assert indent(2, 'abc') == 'abc'


def test_indenting_empty_string():
    assert indent(2, '') == ''


def test_indenting_multiline_string():
    assert indent(4, 'abc\ndef') == '''abc
    def'''
