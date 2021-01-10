#### use `pip2nix` with `nix-shell`

The dependency of python packages is saved in `requirements.txt` in python project.  
At first, there is only `requirements.txt` in the folder.

- generate the `python-packages.nix` by following command
`pip2nix generate -r requirements.txt`

- write down the `shell.nix` as the example, and setup the python with pypi packages

- use `nix-shell` to use python in this shell, by following command
`nix-shell shell.nix`

- now you can use python and import the pypi package(for example, `requests`), 
you will got something like this.
```
[nix-shell:~/pip2nix/examples/shell]$ python
Python 3.8.6 (default, Sep 23 2020, 13:54:27)
[GCC 10.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import requests
>>>
```
