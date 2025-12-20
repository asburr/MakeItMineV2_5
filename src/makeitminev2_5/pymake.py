import os
import re
import datetime
import argparse
import tomllib
from makeitminev2_5.make import Make
from makeitminev2_5.makeutils import MakeUtils


class PyMake(Make,MakeUtils):
  """ Platform independent recipies for a Makefile supporting a Python project. """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.poetry_p = self._cmdstr(["which","poetry"],_show=False)
    if not self.poetry_p:
      raise Exception("Cannot find poetry. Install poetry in a different venv (not this project) using pip install poetry")
    self.venv = self._cmdstr([self.poetry_p,"env","info","--path"],_show=False)
    self.python_p = os.path.join(self.venv,"bin","python")
    self.src = "src"
    self.toml = "pyproject.toml"
    self.download = os.path.join(self.cwd,".download")
    if not os.path.exists(self.download): os.mkdir(self.download)
    self.wheel = os.path.join(self.download,f"{self.name().lower()}-{self.version()}-py3-none-any.whl")
    self.cache = os.path.join(self.cwd,".cache")
    if not os.path.exists(self.cache):
      self._cmd([self.poetry_p,"config","cache-dir",self.cache],_show=False)
      os.mkdir(self.cache)
    self.lockfile = "poetry.lock"

  def _files(self) -> list:
    """ Perminant files that can be created by this class. """
    return super()._files()+[self.toml,self.lockfile]

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

dependencies = [
]
requires-python=">=3.10"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
""")
    self._cmd([self.poetry_p,"add","--group","dev","spyder-kernels==3.1"],_show=True)

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
            for l in f:
              if re.search('^\s*__version__\s*==',l):
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
      with open(p,"w"):
        f.write(text)
    return p

  def pygetpackagedetails(self,package:str) -> dict:
    """ until to read package details from pyprojec.toml. """
    if not os.path.exists(self.toml): return {}
    with open(self.toml, "rb") as f:
        data = tomllib.load(f)
    # Access details under the modern [project] table or legacy [tool.poetry]
    print(data.get("project", data.get("dependencies", {})))

  def pyinstall(self,package:str,version:str=None,internal:bool=False) -> str:
    """ pyproject.toml, venv, and lock file - install package.
        Provide the path when the package is 1st party. It is added to the dev
        group as editable, and the prod group with the pinned version found
        in the local project.
        Without the path, "poetry add package" creates a major constraint in the
        pyproject.toml and lock file. For example, "requests 2.1.1"
        adds a default constraint of "requests^2.1.1" which means any
        version >=2.1.1 and < 3.0.0.
    """
    self.pysyncvenv() # Must sync venv first, before add packages.
    self.pyuninstall(package) # Must uninstall from all groups before adding!
    p=os.path.join("..",package)
    if os.path.exists(p): internal = True
    if internal:
      if os.path.exists(p):
        if not version:
          version = self.version(p)
          if not version:
            print("ERROR: no version found in repo at path")
            os._exit(1)
        self._cmd([self.poetry_p,"add","--group","dev",p,"--editable"],_show=True)
        self._cmd([self.poetry_p,"add","--group","prod",f'"{package}=={version}"'],_show=True)
      else:
        if not version:
          print("ERROR: must specify version or clone repo")
          os._exit(1)
        self._cmd([self.poetry_p,"add","--group","dev",f'"{package}=={version}"'],_show=True)
        self._cmd([self.poetry_p,"add","--group","prod",f'"{package}=={version}"'],_show=True)
      return
    # 3rd party package is added to the main group.
    if not version:
      print("ERROR: must specify version")
      os._exit(1)
    self._cmd([self.poetry_p,"add","--group","main",f'"{package}=={version}"'],_show=True)

  def pyuninstall(self,package:str) -> str:
    """ pyproject.toml, venv, and lock file - remove package. """
    self._cmd([self.poetry_p,"remove",package],fail=False,_show=True)
    self._cmd([self.poetry_p,"remove","--group","dev",package],fail=False,_show=True)
    self._cmd([self.poetry_p,"remove","--group","prod",package],fail=False,_show=True)

  def pyupdateminor(self,package:str) -> str:
    """ venv and lock file - update package to the latest minor version. """
    if package in self._cmd([self.poetry_p,"_show","--only","prod"],_show=True):
      print("ERROR: package is in dev and prod group, use pyadd")
      os._exit(1)
    self._cmd([self.poetry_p,"update",package],_show=True)

  def pyupdatemajor(self,package:str) -> str:
    """ venv and lock file - update package to the latest major version. """
    if package in self._cmd([self.poetry_p,"_show","--only","prod"],_show=True):
      print("ERROR: package is in dev and prod group, use pyadd")
      os._exit(1)    
    self._cmd([self.poetry_p,"add",package],_show=True)

  def pysyncvenv(self) -> None:
    """ Sync pyproject.toml and lockfile and venv, so packages can be added
    and removed.
    Check developer packages for local paths.
    """
    for line in self._cmd([self.poetry_p,"_show","--top-level","--only","dev"],fail=False,_show=True):
      (package,version,*rest) = line.split()
      self._cmd([self.poetry_p,"remove","--group","dev",package],_show=True)
    for line in self._cmd([self.poetry_p,"_show","--top-level","--only","prod"],fail=False,_show=True):
      (package,version,*rest) = line.split()
      p=os.path.join("..",package)
      if os.path.exists(p):
        self._cmd([self.poetry_p,"add","--group","dev",p,"--editable"],_show=True)
      else:
        self._cmd([self.poetry_p,"add","--group","dev",f'"{package}=={version}"'],_show=True)
    if self._cmd([self.poetry_p,"_show","--top-level","--only","dev"],fail=False,_show=True):
      self._cmd([self.poetry_p,"install","--only","main,dev"],_show=True)
    else:
      self._cmd([self.poetry_p,"install","--only","main"],_show=True)

  def pypackage(self) -> None:
    """ Create a Python distribution wheel and tar in download dir. """
    if not self._rebuild_target(self.wheel,[self.toml,"src"]):
      print(f"{self.wheel} is up to date")
      return
    self._cmd([self.poetry_p,"version",self.version()],_show=True)
    self._cmd([self.poetry_p,"lock"],_show=True)
    self.pysyncvenv()
    self._cmd([self.poetry_p,"build","--format","wheel","--output",self.download],_show=True)
    self._touch(self.wheel)

  def pytest(self) -> None:
    """ Run pytest. """
    self.pysyncvenv()
    self._cmd([self.poetry_p,"run","pytest"],_show=True)

  def _upversion(self,version:str,oldversion:str) -> str:
    """ Update python with the build version. """
    self._cmd([self.poetry_p,"version",version],_show=True)

  def _pypackages(self) -> str:
    """ Return when build was last built """
    if not os.path.exists(self.wheel): return "Not packaged"
    o = os.path.getmtime(self.wheel)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - o)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{os.path.basename(self.wheel)}\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"

  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._work_align()+["c"]

  def _workTitles(self) -> list:
    """ Titles for work """
    return super()._workTitles()+["pypackage\nlocal>local\npypackage"]

  def _work(self) -> list:
    """ Gather project work """
    name = self.name()
    p = os.path.join(self.src,name)
    if not os.path.exists(p):
      print(f"ERROR: cannot find source path {p}")
      os._exit(1)
    self.init_dot_py()
    work  = "Not packages" if not os.path.exists(self.wheel) else ""
    return super()._work()+[work]

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    super()._main(ap)
    cls._add_argument(ap,'package', help="Package for pyadd, pyremove, pyupdate",
                      cmds=["pyadd","pyremove","pyupdate","pygetpackagedetails"])
    cls._add_argument(ap,'path', help="Path",cmds=["pyadd"],optional=True)
    cls._add_argument(ap,'pj', help="Path",
                      cmds=["pyproject_dot_toml","pyinit_dot_py_path",
                            "init_dot_py","pygetpackagedetails","pyinstall",
                            "pyuninstall","pyupdateminor","pyupdatemajor",
                            "pysyncvenv","pypackage", "pytest"],
                      optional=True)

if __name__ == "__main__":
  PyMake.main()