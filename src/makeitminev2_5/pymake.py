import os
import re
from pathlib import Path
import datetime
from makeitminev2_5.make import Make
from makeitminev2_5.makeutils import MakeUtils


class PyMake(Make,MakeUtils):
  """ Platform independent recipies for a Makefile supporting a Python project. """

  def _ignorepaths(self) -> list:
    return super()._ignorepaths() + ["venv","__pycache__", "dist"]

  def _checkfile(self,file:str) -> str:
    """ Check Python syntax """
    if file.endswith(".py"):
      ruff = self._cmdstr([self.poetry_p,"run","ruff","check","--quiet","--ignore=E402,F541,E70",file],fail=False,_show=True,stderr=True)
      if ruff: return ruff
      lint = self._cmdstr([self.poetry_p,"run","pylint","--errors-only","--disable=C,R",file],fail=False,_show=True,stderr=True)
      if lint: return lint
    if file == "pyproject.toml":
      r = self._cmdstr([self.poetry_p,"check"],fail=False,_show=True)
      if "All set!" not in r: return r
    return super()._checkfile(file)

  def _release(self) -> None:
    super()._release()

  def _upversionneeded(self) -> bool:
    return super()._upversionneeded()

  def _upversion(self,version:str,oldversion:str) -> None:
    self._cmd([self.poetry_p,"version",version],_show=True)
    super()._upversion(version,oldversion)

  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._work_align()+["l","l"]

  def _workTitles(self) -> list:
    """ Titles for work """
    return super()._workTitles()+[
      "pycheck\nlocal>local\npysync",
      "pypackaged\nlocal>local\npypackage"
    ]

  def _work(self) -> list:
    """ Gather project work """
    name = self.name()
    p = os.path.join(self.src,name)
    if not os.path.exists(p):
      print(f"ERROR: cannot find source path {p}")
      os._exit(1)
    self.init_dot_py()
    packaging = self.pypackageshow()
    check = self.pycheck()
    return super()._work()+[check,packaging]

  ### End framework required implementations.
 
  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.poetry_p = self._cmdstr(["which","poetry"],_show=False)
    if not self.poetry_p:
      raise Exception("Cannot find poetry. Install poetry in a different venv (not this project) using pip install poetry")
    self.venv = self._cmdstr([self.poetry_p,"env","info","--path"],fail=False,_show=False)
    self.python_p = os.path.join(self.venv,"bin","python") if self.venv else ""
    self.src = "src"
    self.toml = "pyproject.toml"
    self.pye2etest_touchfile = os.path.join("tests","e2e",".done.touch")
    self.pyunittest_touchfile = os.path.join("tests","unittest",".done.touch")
    self.download = os.path.join(self.cwd,".download")
    if not os.path.exists(self.download): os.mkdir(self.download)
    self.wheel = os.path.join(self.download,f"{self.name().lower()}-{self.version()}-py3-none-any.whl")
    if False: # Don't change the cache dir.
      self.cache = os.path.join(self.cwd,".cache")
      if not os.path.exists(self.cache):
        self._cmd([self.poetry_p,"config","cache-dir",self.cache],_show=False)
        os.mkdir(self.cache)
    self.lockfile = "poetry.lock"

  def pyproject_dot_toml(self) -> str:
    """ Create pyproject.toml if one does not exists. """
    if os.path.exists(self.toml):
      print(f'{self.toml} exists')
      return
    self.README_dot_txt()
    name = os.path.basename(self.cwd)
    with open(self.toml,"w") as f:
      f.write(f"""
[project]
name="{name}"
version="0.0.1"
description=""
readme="README.md"

# main group - packages installed from pypi and never from a local path.
dependencies = [
]
requires-python=">=3.10"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"

[dependency-groups]
# dev group - packages for pytest and pyintegrationtest and installed from pypi.
dev = []
# inhouse_prod group - inhouse packages used by CI/CD job to install packages from pypi.
inhouse_prod = []
# inhouse_wsdev group - inhouse packages used in development, install packages as editable from local path.
inhouse_wsdev = []
# inhouse_wsprod group - inhouse packages used in development, install wheels from local path to test the production install.
inhouse_wsprod = []
markers = [
  "e2e: end to end testing, or production testing",
  "unit: utin testing"
]
""")
    self._cmd([self.poetry_p,"add","--group","dev","pylint"],_show=True)
    self._cmd([self.poetry_p,"add","--group","dev","ruff"],_show=True)
    self._cmd([self.poetry_p,"add","--group","dev","pytest"],_show=True)
    self._cmd([self.poetry_p,"add","--group","dev","spyder-kernels==3.1"],_show=True)
    placeholder_package = "setuptools" # so groups are not empty.
    self._cmd([self.poetry_p,"add","--group","inhouse_wsdev",placeholder_package],_show=True)
    self._cmd([self.poetry_p,"add","--group","inhouse_wsprod",placeholder_package],_show=True)
    self._cmd([self.poetry_p,"add","--group","inhouse_prod",placeholder_package],_show=True)
    # Note project root is automatically installed as editable when doing poetry install.

  def pyinit_dot_py_path(self) -> str:
    """ Find the path to the project's __init__.py that contains __version__.
        There should only be one.
    """
    i = None
    for root, dirs, files in os.walk("src"):
      for file in files:
        if "__init__.py" == file:
          p=os.path.join(root,file)
          with open(p,"r") as f:
            for line in f:
              if re.search('^\s*__version__\s*==',line):
                if i:
                  print(f"Cannot have two __init__.py both with __version__, please see {i} and {p}")
                else:
                  i=p
    return i

  def init_dot_py(self) -> str:
    """ Create the init.py with __version__ used when importing a package
        i.e. package.__version__.
    """
    name=self.name()
    p=os.path.join(self.src,name,"__init__.py")
    text=f'''
from importlib.metadata import version, PackageNotFoundError
__version__ = version("{name}")
'''
    if os.path.exists(p):
      if not self._grep(p,"__version__"):
        with open(p,"a") as f:
          f.write(text)
      else:
        t = 'version\("'+name+'"\)'
        if not self._grep(p,t):
          print(f"ERROR: incorrect package name in {p}, expecting {t}, BUILD_VERISON.txt has the name '{name}'")
          os._exit(1)
    else:
      with open(p,"w") as f:
        f.write(text)
    return p

  def pyinstall(self,package:str,version:str=None) -> str:
    """ install a package into pyproject.toml, venv, and lock file.
        :param package: name of the package to install. Locally installed when package is detected by "wspackage".
        :param version: defaults to latest version in pypi, or the version of the local package. When version is specified it must exist in pypi, or must match the version in the local package.
        Note that for 3rdparty packages, poetry creates a major constraint in
        pyproject.toml and lock file. A major constraint for "requests 2.1.1"
        is "requests^2.1.1" which means any version >=2.1.1 and < 3.0.0.
    """
    self.pysync() # Sync venv first before add packages.
    self.pyuninstall(package) # Uninstall the package from all groups before adding.
    p = self.findproject(name=package) # Look for a local package.
    if p:
      # Local package.
      cwd = Path.cwd()
      os.chdir(p)
      v = self.version()
      if v != version:
        print(f"warning: {package} local version is {v}")
        version = v
      wheel = f"{p}/dist/{package}-{version}-py3-none-any.whl"
      if not os.path.exists(wheel):
        print(f"warning: {wheel} does not exit")
        self.pypackage()
      os.chdir(cwd)
      self._cmd([self.poetry_p,"add","--group","inhouse_wsdev",p,"--editable"],_show=True)
      self._cmd([self.poetry_p,"add","--group","inhouse_wsprod",wheel],_show=True)
      self._cmd([self.poetry_p,"add","--group","inhouse_prod",f'"{package}=={version}"'],_show=True)
      return
    # pypi package.
    if version:
      self._cmd([self.poetry_p,"add","--group","main",f'"{package}=={version}"'],_show=True)
    else:
      self._cmd([self.poetry_p,"add","--group","main",package],_show=True)

  def pyuninstall(self,package:str) -> str:
    """ pyproject.toml, venv, and lock file - remove package. """
    print(self._cmdstr([self.poetry_p,"remove",package],fail=False,_show=True,stderr=True))
    print(self._cmdstr([self.poetry_p,"remove","--group","dev",package],fail=False,_show=True,stderr=True))
    print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_wsdev",package],fail=False,_show=True,stderr=True))
    print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_wsprod",package],fail=False,_show=True,stderr=True))
    print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_prod",package],fail=False,_show=True,stderr=True))

  def pyupdateminor(self,package:str) -> str:
    """ venv and lock file - update package to the latest minor version. """
    if package in self._cmd([self.poetry_p,"_show","--only","internal_prod"],_show=True):
      print("ERROR: package is in dev and prod group, use pyadd")
      os._exit(1)
    self._cmd([self.poetry_p,"update",package],_show=True)

  def pyupdatemajor(self,package:str) -> str:
    """ venv and lock file - update package to the latest major version. """
    if package in self._cmd([self.poetry_p,"_show","--only","internal_prod"],_show=True):
      print("ERROR: package is in dev and prod group, use pyadd")
      os._exit(1)    
    self._cmd([self.poetry_p,"add",package],_show=True)

  def pysync(self) -> None:
    """ Sync pyproject.toml and lockfile and venv. With editable and
    non-editable packages found in the inhouse package groups of
    inhouse_wsdev (editable) and inhouse_wsprod (non-editable).
    Warning: will remove packages not installed with pyinstall.
    """
    self._cmdInteractive([self.poetry_p,"lock"],_show=True)
    self._cmdInteractive([self.poetry_p,"sync","--with","dev,inhouse_wsdev,inhouse_wsprod"],_show=True)

  def pycheck(self) -> str:
    """ Check sync of pyproject.toml and lockfile and venv. """
    status = []
    # --lock check for a lock.file.
    r = self._cmdstr([self.poetry_p,"check","--lock"],fail=False,_show=False)
    if not r: status.append("Missing lock")
    elif "All set" not in r: status.append("toml ahead of lock")
    r = self._cmdstr([self.poetry_p,"sync","--dry-run","--with","dev,inhouse_wsdev,inhouse_wsprod"],fail=False,_show=False)
    if not r or "0 installs, 0 updates, 0 removals" not in r: status.append("lock ahead of venv")
    return "\n".join(status)

  def pypackageshow(self) -> str:
    """ Check if package needs rebuilding. """
    if not os.path.exists(self.wheel):
      return "No package"
    if self._rebuild_target(self.wheel,[self.toml,"src"],msg=False):
      return "package behind source\n"+self.pypackaged()
    return ""

  def pypackage(self) -> None:
    """ Create a Python distribution wheel and tar in dist dir. """
    if not self._rebuild_target(self.wheel,[self.toml,"src"]):
      print(f"{self.wheel} is up to date")
      return
    self._cmd([self.poetry_p,"version",self.version()],_show=True)
    self._cmd([self.poetry_p,"build","--format","wheel","--output",self.download],_show=True)
    self._touch(self.wheel)

  def pyunittest(self) -> None:
    """ Run pytest unittests. """
    if not self._rebuild_target(
        self.pyunittest_touchfile,
        [self.toml,"src","docker","example"]):
      return
    self.pysync()
    self._cmd([self.poetry_p,"run","pytest","-s","-m","unit"],_show=True)
    self._touch(self.pyunittest_touchfile)

  def pye2etest(self) -> None:
    """ Run pytest e2e tests. """
    if not self._rebuild_target(
        self.pye2etest_touchfile,
        [self.toml,"src","docker","example"]):
      return
    self.pysync()
    # -s to show stdout.
    # -vv stops output being truncated when tests fail and help debugging.
    self._cmdInteractive([self.poetry_p,"run","pytest","-vv","-s","-m","e2e"],_show=True)
    self._touch(self.pye2etest_touchfile)

  def pypackaged(self) -> str:
    """ Return when build was last built """
    if not os.path.exists(self.wheel): return "Not packaged"
    o = os.path.getmtime(self.wheel)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - o)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{os.path.basename(self.wheel)}\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"


if __name__ == "__main__":
  PyMake.main()