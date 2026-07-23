import os
import re
from pathlib import Path
import datetime
from makeitminev2_5.abc_make import _ABCMake
from makeitminev2_5.makeutils import _MakeUtils


class PyMake(_ABCMake,_MakeUtils):
  """
  Python with venv and packaging and code beautify and type checking and
  unit and e2e tests.
  
  The mechanics of Python is by one of the following: Poetry or Pip or UV.
  
  ruff is used to beautify the code.
  
  vt does type checking.
  
  pytest for the testing.
  """

  _name = "py"
  _fullname = "python"
  _active_default = False

  _PYMECHANICS = "mechanics"
  _PYPOETRY = "poetry"
  _PYPIP = "pip"
  _PYUV = "uv"

  def _ignorepaths(self) -> list:
    return super()._ignorepaths() + ["venv","__pycache__", "dist"]

  def _checkfile(self,file:str) -> str:
    """ Check Python syntax """
    if file.endswith(".py"):
      self.sync()
      ruff = self._cmdstr([os.path.join(self.venv_bin,"ruff"),"check","--quiet","--ignore=E402,F541,E70",file],fail=False,_show=True,stderr=True)
      if ruff: return ruff
      typecheck = self._cmdstr([os.path.join(self.venv_bin,"ty"),"check",file],fail=False,_show=True,stderr=True)
      if typecheck: return typecheck
    if file == "pyproject.toml":
      if self._mechanics == PyMake._PYPOETRY:
        r = self._cmdstr([self.poetry_p,"check"],fail=False,_show=True)
        if "All set!" not in r: return r
      elif self._mechanics in [PyMake._PYPIP, PyMake._PYUV]:
        r = self._cmdstr([os.path.join(self.venv_bin,"validate-pyproject"),file],fail=False,_show=True,stderr=True)
        if "All set!" not in r: return r
      else:
        self._stopmechanics()
    return super()._checkfile(file)

  def _release(self) -> None:
    super()._release()

  def _upversionneeded(self) -> bool:
    return super()._upversionneeded()

  def _upversion(self,version:str,oldversion:str) -> None:
    if self._mechanics == PyMake._PYPOETRY:
      self._cmd([self.poetry_p,"version",version],_show=True)
    elif self._mechanics in [PyMake._PYPIP, PyMake._PYUV]:
      r = self._cmdstr([
        os.path.join(self.venv_bin,"toml"),
        "set",
        "--toml-path=pyproject.toml",
        "project.version",version],
        fail=False,_show=True,stderr=True)
      if "All set!" not in r: return r
    else:
      self._stopmechanics()
    super()._upversion(version,oldversion)

  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._work_align()+["l","l"]

  def _workTitles(self) -> list:
    """ Titles for work """
    return super()._workTitles()+[
      f"{PyMake._name} check\nlocal>local\n{PyMake._name} sync",
      f"{PyMake._name} packagedshow\nlocal>local\n{PyMake._name} package"
    ]

  def _work(self) -> list:
    """ Gather project work """
    name = self.name()
    p = os.path.join(self.pysrc,name)
    if not os.path.exists(p):
      print(f"INFO creating {p}")
      os.mkdir(self.pysrc)
      os.mkdir(p)
      for name in os.listdir(path="."):
        if os.path.isfile(name) and name.endswith(".py"):
          fp = os.path.join(p,name)
          print(f"INFO: moving {name} to {p}")
          os.rename(name,fp)
    self.init_dot_py()
    self.pyproject_dot_toml()
    packaging = self.packageshow()
    check = self.check()
    return super()._work()+[check,packaging]

  def create_files(self):
    super().create_files()
    self.pyproject_dot_toml()
    self.init_dot_py()

  ### End framework required implementations.
 
  def mechanics(self,mechanics:str):
    """
    Select the Python mechanic. Choices are Poetry, Pip, or Uv. They support
    the same features.
    
    Uv starts quickly due to being compiled code whereas poetry and pip are
    python. Uv installs quickly due to the venv having links to the cached
    packages, whereas poetry and pip copy the packages into the venv which is
    both slower and takes up more disk space. TODO: is there an option in
    Poetry to link to the cache rather than copy on the install????

    Note that Uv "workspace" and poetry "packageless project" is about multiple
    packages sharing a lockfile and venv. The multiple packages are in a
    monorepo which has a subdir per package. One of the packages
    is built for release, the other packages exist to support the released
    package. It is possible with Poetry to release more than one package, but
    is not recommended as an up-version of a common dependency makes an
    unnecessary change and unacceptable release of the other package. In this
    case the packages need to be in separate repos with their own lockfile.
    """
    if mechanics not in [PyMake._PYPIP,PyMake._PYPOETRY,PyMake._PYUV]:
      self.stop(f"mechanics are {PyMake._PYPIP} or {PyMake._PYPOETRY} or {PyMake._PYUV}")
    self._setpreference(PyMake._PYMECHANICS,mechanics)

  def _stopmechanics(self):
    self.stop(f"please specify python mechanics using, MIM py mechanics <{PyMake._PYPIP}, {PyMake._PYPOETRY}, or {PyMake._PYUV}>")
    
  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self._mechanics = self._getpreference(PyMake._PYMECHANICS)
    #if self._mechanics is None:
    #  self.stop("Select python mechanics using pypoetry or pypip or pyuv")
    self.venv = None
    if self._mechanics == PyMake._PYPOETRY:
      self.poetry_p = self._cmdstr(["which","poetry"],_show=False)
      if not self.poetry_p:
        self.stop("Cannot find poetry. Install poetry in a different venv (not this project) using pip install poetry")
      self.venv = self._cmdstr([self.poetry_p,"env","info","--path"],fail=False,_show=False)
      self.venv_bin = os.path.join(self.venv,"bin")
    elif self._mechanics == PyMake._PYPIP:
      self.venv = os.path.join(self.cwd,"venv")
      self.venv_bin = os.path.join(self.venv,"bin")
    elif self._mechanics == PyMake._PYUV:
      self.uv_p = self._cmdstr(["which","uv"],_show=False)
      if not self.uv_p:
        self.stop("Cannot find uv. Install uv in a different venv (not this project) using pip install uv")
      a = self._cmdstr([self.uv_p,"python","find"],fail=False,_show=False).split(os.path.sep)
      self.venv_bin = os.path.join(a[:-1])
      self.venv = os.path.join(a[:-2])
      pass # TODO;
    self.python_p = os.path.join(self.venv,"bin","python") if self.venv else ""
    self.pysrc = "src"
    self.toml = "pyproject.toml"
    self.pye2etest_touchfile = os.path.join("tests","e2e",".done.touch")
    self.pyunittest_touchfile = os.path.join("tests","unittest",".done.touch")
    self.dist = os.path.join(self.cwd,".dist")
    if not os.path.exists(self.dist): os.mkdir(self.dist)
    self.wheel = os.path.join(self.dist,f"{self.name().lower()}-{self.version()}-py3-none-any.whl")
    if self._mechanics == PyMake._PYPOETRY:
      if False: # Don't change the cache dir.
        self.cache = os.path.join(self.cwd,".cache")
        if not os.path.exists(self.cache):
          self._cmd([self.poetry_p,"config","cache-dir",self.cache],_show=False)
          os.mkdir(self.cache)
      self.lockfile = "poetry.lock"
    elif self._mechanics == PyMake._PYPIP:
      self.lockfile = "requirements.txt"
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;

  def info(self):
    """ Show the path to python for venv. """
    print(f"Mechanics: {self._mechanics}")
    print(f"Venv: {self.venv}")
    print(f"Interpreter: {self.python_p}")

  def pyproject_dot_toml(self) -> str:
    """ Create pyproject.toml if one does not exists. """
    self.README_dot_txt()
    if not self._rebuild_target(self.toml,[]): return
    name = os.path.basename(self.cwd)
    placeholder_package = "setuptools" # so groups are not empty.
    # dev group - packages for pytest and pyintegration test and installed from pypi.
    dev_deps = ["pylint","ruff","pytest","pytest-dependency","spyder-kernels==3.1"]
    with open(self.toml,"w") as f:
      f.write(f"""
[project]
name="{name}"
version="0.0.1"
description=""
readme="README.md"
requires-python=">=3.10"

[tool.pytest.ini_options]
markers = [
  "e2e: end to end testing, or production testing",
  "unit: unit testing"
]
""")
    if self._mechanics == PyMake._PYPOETRY:
      with open(self.toml,"a") as f:
        f.write("""

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
""")
      for dep in dev_deps:
        self._cmd([self.poetry_p,"add","--group","dev",dep],_show=True)
      # inhouse_prod group - inhouse packages used by CI/CD job to install packages from pypi.
      # inhouse_wsdev group - inhouse packages used in development, install packages as editable from local path.
      # inhouse_wsprod group - inhouse packages used in development, install wheels from local path to test the production install.
      self._cmd([self.poetry_p,"add","--group","inhouse_wsdev",placeholder_package],_show=True)
      self._cmd([self.poetry_p,"add","--group","inhouse_wsprod",placeholder_package],_show=True)
      self._cmd([self.poetry_p,"add","--group","inhouse_prod",placeholder_package],_show=True)
      # Note project root is automatically installed as editable when doing poetry install.
    elif self._mechanics == PyMake._PYPIP:
      dependencies="dependencies = ["
      with open(self.toml,"a") as f:
        f.write(f"""

{dependencies}
  "{placeholder_package}"
]
""")
      for dep in dev_deps:
        _MakeUtils._sedAfter(fn=self.toml,after=dependencies,s=f"""  "{dep}",\n""")
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()

  def init_dot_py_path(self) -> str:
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
    p=os.path.join(self.pysrc,name,"__init__.py")
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
          _MakeUtils.stop(f"ERROR: incorrect package name in {p}, expecting {t}, BUILD_VERISON.txt has the name '{name}'")
    else:
      with open(p,"w") as f:
        f.write(text)
    return p

  def wheel(self) -> str:
    """ Return the path to the wheel. """
    return os.path.join(
      Path.cwd(),self.dist,f"{self.name()}-{self.version()}-py3-none-any.whl")

  def install(self,package:str,version:str=None,root:str=None) -> str:
    """ install a package into pyproject.toml, venv, and lock file.
        :param package: name of the package to install. Locally installed when package is detected by "wspackage".
        :param version: defaults to latest version in pypi, or the version of the local package. When version is specified it must exist in pypi, or must match the version in the local package.
        :param root: root of the project to install but default is CWD or in workspace if using those.
        Note that for 3rdparty packages, poetry creates a major constraint in
        pyproject.toml and lock file. A major constraint for "requests 2.1.1"
        is "requests^2.1.1" which means any version >=2.1.1 and < 3.0.0.
    """
    if self.name() == package:
      _MakeUtils.stop(f"ERROR:Cannot install {package} to the project with the same name.")
    p = self.findproject(name=package,root=root) # Look for a local package.
    self.sync() # Sync venv first before add packages.
    self.pyuninstall(package) # Uninstall the package from all groups before adding.
    if self._mechanics == PyMake._PYPOETRY:
      if p:
        # Local package.
        cwd = Path.cwd()
        os.chdir(p)
        v = self.version()
        if v != version:
          print(f"warning: {package} local version is {v}")
          version = v
        self.package()
        wheel = self.pywheel()
        if not os.path.exists(wheel):
          _MakeUtils.stop(f"ERROR: {wheel} does not exit")
        os.chdir(cwd)
        self._cmd([self.poetry_p,"add","--group","inhouse_wsdev",p,"--editable"],fail=True,_show=True)
        self._cmd([self.poetry_p,"add","--group","inhouse_wsprod",wheel],fail=True,_show=True)
        self._cmd([self.poetry_p,"add","--group","inhouse_prod",f'"{package}=={version}"'],fail=True,_show=True)
        return
      # pypi package.
      if version:
        self._cmd([self.poetry_p,"add","--group","main",f'"{package}=={version}"'],fail=True,_show=True)
      else:
        self._cmd([self.poetry_p,"add","--group","main",package],fail=True,_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()

  def uninstall(self,package:str) -> str:
    """ pyproject.toml, venv, and lock file - remove package. """
    if self._mechanics == PyMake._PYPOETRY:
      print(self._cmdstr([self.poetry_p,"remove",package],fail=False,_show=True,stderr=True))
      print(self._cmdstr([self.poetry_p,"remove","--group","dev",package],fail=False,_show=True,stderr=True))
      print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_wsdev",package],fail=False,_show=True,stderr=True))
      print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_wsprod",package],fail=False,_show=True,stderr=True))
      print(self._cmdstr([self.poetry_p,"remove","--group","inhouse_prod",package],fail=False,_show=True,stderr=True))
    else:
      self._stopmechanics()

  def python(self) -> None:
    """ Opens a python shell in the projects venv """
    print("quit() to quit the shell")
    if self._mechanics == PyMake._PYPOETRY:
      self._cmdInteractive([self.poetry_p,"run","python"],_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()

  def sync(self) -> None:
    """ Sync pyproject.toml and lockfile and venv. With editable and
    non-editable packages found in the inhouse package groups of
    inhouse_wsdev (editable) and inhouse_wsprod (non-editable).
    Warning: will remove packages not installed with pyinstall.
    """
    self.pyproject_dot_toml()
    if self._mechanics == PyMake._PYPOETRY:
      self._cmdInteractive([self.poetry_p,"lock"],_show=True)
      self._cmdInteractive([self.poetry_p,"sync","--with","dev,inhouse_wsdev,inhouse_wsprod"],_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()

  def check(self) -> str:
    """ Check sync of pyproject.toml and lockfile and venv. """
    status = []
    # --lock check for a lock.file.
    if not os.path.exists(self.toml):
      status.append("Missing pyproject.toml")      
    if self._mechanics == PyMake._PYPOETRY:
      r = self._cmdstr([self.poetry_p,"check","--lock"],fail=False,_show=False)
      if not r: status.append("Missing lock")
      elif "All set" not in r: status.append("toml ahead of lock")
      r = self._cmdstr([self.poetry_p,"sync","--dry-run","--with","dev,inhouse_wsdev,inhouse_wsprod"],fail=False,_show=False)
      if not r or "0 installs, 0 updates, 0 removals" not in r: status.append("lock ahead of venv")
      return "\n".join(status)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()

  def packageshow(self) -> str:
    """ Check if package needs rebuilding. """
    if not os.path.exists(self.wheel):
      return "No package"
    p = self._rebuild_target(self.wheel,[self.toml,"src"],msg=False)
    if p:
      return f"package behind source ({p})\n"+self.packagedshow()
    return ""

  def package(self) -> None:
    """ Create a Python distribution wheel and tar in dist dir. """
    if not self._rebuild_target(self.wheel,[self.toml,"src"]):
      print(f"{self.wheel} is up to date")
      return
    if self._mechanics == PyMake._PYPOETRY:
      self._cmd([self.poetry_p,"version",self.version()],_show=True)
      self._cmd([self.poetry_p,"build","--format","wheel","--output",self.dist],_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()
    self._touch(self.wheel)

  def unittest(self) -> None:
    """ Run pytest unittests. """
    if not self._rebuild_target(
        self.pyunittest_touchfile,
        [self.toml,"src"]):
      return
    self.sync()
    if self._mechanics == PyMake._PYPOETRY:
      self._cmd([self.poetry_p,"run","pytest","-s","-m","unit"],_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()
    self._touch(self.pyunittest_touchfile)

  def e2etest(self) -> None:
    """ Run pytest e2e tests. """
    if not self._rebuild_target(
        self.pye2etest_touchfile,
        [self.toml,"src"]):
      return
    self.sync()
    # -s to show stdout.
    # -vv stops output being truncated when tests fail and help debugging.
    if self._mechanics == PyMake._PYPOETRY:
      self._cmdInteractive([self.poetry_p,"run","pytest","-vv","-s","-m","e2e"],_show=True)
    elif self._mechanics == PyMake._PYPIP:
      pass # TODO;
    elif self._mechanics == PyMake._PYUV:
      pass # TODO;
    else:
      self._stopmechanics()
    self._touch(self.pye2etest_touchfile)

  def packagedshow(self) -> str:
    """ Return when build was last built """
    if not os.path.exists(self.wheel): return "Not packaged"
    o = os.path.getmtime(self.wheel)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - o)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{os.path.basename(self.wheel)}\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"