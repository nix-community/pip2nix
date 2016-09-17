import json

from pip2nix.models import package


def test_get_nix_licenses():
    licenses = package.get_nix_licenses()
    assert 'gpl3' in licenses


def raise_on_call(*args, **kwargs):
    raise Exception("Must not be called")


def test_loads_data_once(monkeypatch):
    stub_data = {'stub': {'attr': 'value'}}
    stub_value = json.dumps(json.dumps(stub_data)).encode('utf-8')
    package._nix_licenses = None

    monkeypatch.setattr(package, 'check_output', lambda *args: stub_value)
    package.get_nix_licenses()
    monkeypatch.setattr(package, 'check_output', raise_on_call)
    package.get_nix_licenses()

    assert package._nix_licenses == stub_data
