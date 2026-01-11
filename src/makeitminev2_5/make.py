from abc import ABC, abstractmethod
import os
import re
import json
from pathlib import Path
from makeitminev2_5.ap_decorator import ap_decorator_main, ap_decorator_runcmd
from makeitminev2_5.makeutils import MakeUtils


class Make(ABC,MakeUtils):
  """ MakeItMine framework """
  
  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.preferences = os.path.join(Path.home(),".makeitmine.json")

  @abstractmethod
  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return []

  @abstractmethod
  def wspjpath(self,pj:str) -> str:
    """ Project is part of the users workspace and project is
    available locally at the returned path.
    :param pj: project name.
    """
    return None

  @abstractmethod
  def _checkfile(self,file:str) -> bool:
    """ Check the syntax and semantics in a file """
    if file.endswith(".json"):
      with open(file,"r",encoding='utf-8') as f:
        try:
          json.load(f)
        except Exception as e:
          print(f"{file} bad json syntax error is {e}")
          return False
    return True

  def checkfile(self,file:str) -> bool:
    """ Check the syntax in a file
    :param file: Path to the file to be checked
    """
    touch = os.path.join(os.path.dirname(file),f".{os.path.basename(file)}.touch")
    if not self._rebuild_target(touch,[file]): return True
    r = self._checkfile(file)
    self._touch(touch)
    return r

  @abstractmethod
  def _release(self) -> None:
    """ Release a project. """
    pass

  @abstractmethod
  def _upversionneeded(self) -> bool:
    """ Is up version needed. """
    pass

  @abstractmethod
  def _upversion(self,version:str,oldversion:str) -> None:
    """ Up version the project. """
    pass

  @abstractmethod
  def _workTitles(self) -> list:
    """ Titles for work """
    return []

  @abstractmethod
  def _work(self) -> list:
    """ Gather project work """
    return []

  @abstractmethod
  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return []

  @classmethod
  def main(cls):
    ap_decorator_main(cls)
    ap_decorator_runcmd(cls)

  def getpreference(self,key:str) -> str:
    """ Preferences are stored in home/.makeitmine.json
    :param key: Key to preference
    :return: value for the key or None.
    """
    if not os.path.exists(self.preferences): return None
    try:
      with open(self.preferences,"r") as f:
        j = json.load(f)
        return j.get(key,f)
    except Exception as e:
      print(f"ERROR: {self.preferences} is corrupt {e}")

  def setpreference(self,key:str,value:str) -> None:
    """ Preferences are stored in home/.makeitmine.json
    :param key: Key to preference
    :param value: Value for key.
    """
    if os.path.exists(self.preferences):
      with open(self.preferences,"w") as f:
        json.dump({key:value},f)
    else:
      with open(self.preferences,"r") as f:
        j = json.load(f)
        j[key]=value
        json.dump(f,j)

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

  def findproject(self,name:str,version:str=None,path:str=None) -> str:
    """ Find a project in the users home directory.
    :param name: Name of the project.
    :param version: Version of the project.
    :return path: path to the project.
    """
    if not path: path=Path.home()
    ignore = self.ignorepaths()
    for e in os.listdir(path):
      p = os.path.join(path,e)
      if os.path.isfile(p):
        if e != self.bv: continue
        os.chdir(path)
        if self.name() == name:
          if version and self.version() != version:
            print(f"{path} has version {self.version()} expecting to find {version}")
            os._exit(1)
          return path
        os.chdir(self.cwd)
        return None # This is a project root, don't scan subdirs.
      else:
        if e.startswith("."): continue
        if e in ignore: continue
        p = self.findproject(name,version,path=p)
        if p: return p
    
  def README_dot_txt(self) -> None:
    """ Creates the standard README.md. """
    if os.path.exists(self.readme):
      return
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
