import importlib.resources


def read_text(name):
    return (importlib.resources.files("pip2nix") / name).read_text(encoding="utf-8")
