import os
import re
import json
from pathlib import Path
from makeitminev2_5.abc_make import _ABCMake
from makeitminev2_5.makeutils import _MakeUtils


class Make(_ABCMake, _MakeUtils):
  """
  MakeItMine framework.
  
  Each class is a recipe and methods are automatically added to the CLI as
  targets under the recipe. Method needs a docstring and no underscore in the
  method name, the CLI excludes inherited methods.
  
  BUILDVERSION.txt contains a text representation of the version using the format
  of major.minor.build. Make creates the initial version. "name" and
  "version" access the project name and version.
  
  README.txt is the standard file. Make creates the inital README.
  """

  """ Add Make to prj, """
  _name = "prj"
  _fullname = "project"
  _active_default = True
  
  """ Must implement the framework. """
  def _release(self) -> None: return super()._release()
  def _ignorepaths(self) -> list: return super()._ignorepaths()
  def _checkfile(self,file:str) -> str: return super()._checkfile(file)
  def _upversionneeded(self) -> bool: super()._upversionneeded()
  def _upversion(self,version:str,oldversion:str) -> None: super()._upversion(version,oldversion)
  def _workTitles(self) -> list: return super()._workTitles()
  def _work(self) -> list: return super()._work()
  def _work_align(self) -> list: return super()._work_align()

  bv = "BUILD_VERSION.txt"
  readme = "README.md"
  
  def checkfile(self,file:str) -> str:
    """ Check the syntax in a file
    :param file: Path to the file to be checked
    """
    touch = os.path.join(os.path.dirname(file),f".{os.path.basename(file)}.touch")
    if not self._rebuild_target(touch,[file]): return None
    r = self._checkfile(file)
    if not r: self._touch(touch)
    return r

  def _classActivateCheck(cls,func):
      """ Check if class is active."""
      def wrapper(*args, **kwargs):
        class_name = func.__qualname__.split(".")[0]
        name = globals()[class_name]._name
        if cls._getpreference(name,False) == False:
          print(f"{name} is not active")
          return None
        return func(*args, **kwargs)
      return wrapper
  
  def _classActivation(cls):
    """ Wraps each method with a check that that class is activated.
    """
    for name in dir(cls):
      if name.startswith("_"): continue
      func = getattr(cls,name)
      if not callable(func): continue
      setattr(cls, name, cls._classActivateCheck(func))
      return cls

  def activate(self,name:str):
    """ Activate recipes.
    :param name: recipes to activate
    """
    if self._getpreference(name) is None:
      print(f"{name} no such service")
      return
    if self._getpreference(name) is True:
      print(f"{name} is already activated")
      return
    self._setpreference(name, True)

  def deactivate(self,name:str):
    """ Deactivate recipes.
    :param name: recipe to deactivate
    """
    if self._getpreference(name) is None:
      print(f"{name} no such service")
      return
    if name in [self._name,]:
      print(f"Cannot deactivate {name}")
      return
    if not self._getpreference(name) is False:
      print(f"{name} is already deactivated")
      return
    self._setpreference(name, False)

  def info(self):
    """ Show preferences """
    print(f"Preferences: {self.preferences}")
    if os.path.exists(self.preferences):
      with open(self.preferences,"r") as f:
        j = json.load(f)
        print(json.dumps(j,indent=5))
    
  def ignorepaths(self) -> list:
    """ List of paths to ignore """
    return self._ignorepaths()

  def BUILDVERSION_dot_txt(self) -> None:
    """ Create the initial build version file. """
    p=os.path.join(self.cwd,self.bv)
    if not os.path.exists(p):
      name = os.path.basename(os.path.dirname(p))
      with open(p,"w") as f:
        f.write(f"{name}:0.0.1{os.linesep}")

  def name(self) -> str:
    """ Get project name """
    self.BUILDVERSION_dot_txt()
    p=os.path.join(self.cwd,self.bv)
    with open(p,"r") as f:
      for line in f:
        m = re.search('^(.*):(.*)',line)
        if m:
          return m.group(1)

  def version(self) -> str:
    """ Get project version """
    self.BUILDVERSION_dot_txt()
    p=os.path.join(self.cwd,self.bv)
    with open(p,"r") as f:
      for line in f:
        m = re.search('^(.*):(.*)',line)
        if m:
          return m.group(2)

  def changeversion(self,pos:str="build",down:bool=False):
    """ Increment or decrement the project version of major, minor, or build. """
    name = self.name()
    oldversion = self.version()
    a = [int(x) for x in oldversion.split(".")]
    if pos == "major": a[0] += -1 if down else 1
    elif pos == "minor": a[1] += -1 if down else 1
    elif pos == "build": a[2] += -1 if down else 1
    else: raise Exception(f"Unknown pos {pos}")
    version = ".".join(a)
    p=os.path.join(self.cwd,f".{self.bv}")
    with open(p,"w") as f: f.write(f"{name}:{version}")
    self.syncversion()

  def syncversion(self):
    """ Synchronize BUILD_VERSION with other recipes. """
    version = self.version()
    self._upversion(version,version)

  def _findproject(self,name:str,version:str=None,root:str=None) -> str:
    """ Find a project in the users home directory.
    :param name: Name of the project.
    :param version: Version of the project.
    :param root: Where to start looking for the project, will search subdirs.
    """
    if not root: root=Path.home()
    ignore = self.ignorepaths()
    for e in os.listdir(root):
      p = os.path.join(root,e)
      if os.path.isfile(p):
        if e != self.bv: continue
        os.chdir(root)
        n = self.name()
        if n == name: return root
        os.chdir(self.cwd)
        return None # This is a project root, don't scan subdirs.
      elif os.path.isdir(p):
        if e.startswith("."): continue
        if e in ignore: continue
        p = self._findproject(name,version,root=p)
        if p: return p

  def findproject(self,name:str,version:str=None,root:str=None) -> str:
    """ Find a project in the users workspace.
    :param name: Name of the project.
    :param version: Version of the project.
    :param root: search from this root otherwise root is home dir.
    """
    p = self._findproject(name,version,root)
    if p:
      if version:
        os.chdir(p)
        if self.version() != version:
          assert not True, f"{p} has version {self.version()} expecting to find {version}"
    return p

  def README_dot_txt(self) -> None:
    """ Creates the standard README.md. """
    if not self._rebuild_target(self.readme,[]): return
    with open(self.readme,"w") as f:
      f.write("""
# Project Title
Simple overview of use/purpose.
## Description
An in-depth paragraph about your project and overview of use.
## Getting Started
### Dependencies
* Describe any prerequisites, libraries, OS version, etc., needed before installing program.
* ex. Windows 10
### Installing
* How/where to download your program
* Any modifications needed to be made to files/folders
### Executing program
* How to run the program
* Step-by-step bullets
```
code blocks for commands
```
## Help
Any advise for common problems or issues.
```
command to run if program contains helper info
```
## Version History
* 0.2
  * Various bug fixes and optimizations
  * See [commit change]() or See [release history]()
* 0.1
  * Initial Release
## License
This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details
      """)