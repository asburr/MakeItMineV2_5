# pymake (python make)

## Intro
Poetry is the standard tool to ensure reproducible builds.
Python packages are versioned using a string of dot separated characters, 
generally the version is digits of the format Major.Minor.Patch.
# Workflow
```

```
## Leverage the standard module to dynamically maintain version in __version__.
For Poetry to build the package it requires a static version in pyproject.toml.
Standard Poetry does not dynamically update the package __version__ variable.
"importlib" is a standard way of doing this.
````
Dynamic versioning in: __init__.py.
import importlib.metadata
__version__ = importlib.metadata.version("packagename")
```
# No up-versioning during development, only up-version when releasing.

"make pjdone": does not upversion, makes the local repo using the prior version with no cascading during development.
"make gtrelease": upversion the patch level in BUILD_VERSION.txt if the same version in on the main branch. Automatic sync/edit version in pyproject.toml, Dockerfile, docker_compose.yaml, and release.env. Push version changes to remote branch. Merge the remote branch into main. Tag the main branch with the version.
note: Cascading the version to dependents is solely a developer responsibility without any help from the makefile.

# poetry to generate a lock file.

"make pyadd package": calls "poetry add package" which creates a major constraint in the pyproject.toml as well as the locked version.
For example, "make pyadd requests==2.1.1" adds a default constraint of "requests^2.1.1" which means any version >=2.1.1 and < 3.0.0.
"make pyremove package": calls "poetry remove package" which updates pyproject.toml and lockfile.
"make pybuild": calls "poetry install" to sync the venv with the lock-file before building with poetry by calling "poetry build".
"make pyupdateminor package": calls "poetry update package" to update the package to the lastest compatible version within the major constraint.
"make pyupdatelatest package": calls "poetry add package" which updates to the latest version and sets the constraints correctly.

# Upversion on releasing changes to main.
The makefile would have to change the version in pyproject.toml. Poetry also
requires “poetry lock” to be run every time the pyproject.toml has changed,
even when the dependencies have not changed, still poetry checks the timestamps
of both files and warns if the pyproject.toml is newer, and the makefile must
run “poetry lock” to avoid this warning.

# Dependency management across repos.

The standard approach is a private pypi. The private pypi has only one version of each package, the version that is known to work with the other packages in the private pypi. All projects are built using the same private pypi thus ensuring consistent dependency management.
Non-standard options,
vu workspace is used to manage dependency management across repos with a lock file in the root of the workspace which manages all dependencies for the repos in the workspace.
A common requirement.txt shared across the repos with the downfall that packages are installed in a repo regardless if they are needed.
