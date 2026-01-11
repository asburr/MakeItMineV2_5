# pymake (python make)

## Leverage the standard module to dynamically maintain version in __version__.
For Poetry to build the package it requires a static version in pyproject.toml.
Standard Poetry does not dynamically update the package __version__ variable.
"importlib" is a standard way of doing this.
````
Dynamic versioning in: __init__.py.
import importlib.metadata
__version__ = importlib.metadata.version("packagename")
```