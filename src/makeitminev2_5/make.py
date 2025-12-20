from abc import ABC, abstractmethod
import os
import re
from makeitminev2_5.ap_decorator import ap_decorator_main, ap_decorator_runcmd


class Make(ABC):
  """ MakeItMine framework """
  
  @abstractmethod
  def _newfile(self,file:str) -> None:
    """ Adds a new file to the project. """
    pass

  @abstractmethod
  def _build(self) -> None:
    """ build the project. """
    pass

  @abstractmethod
  def _test(self) -> None:
    """ test the project """
    pass

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
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(1)

  def version(self) -> str:
    """ Get project version """
    self.BUILDVERSION_dot_txt()
    p=os.path.join(self.cwd,self.bv)
    with open(p,"r") as f:
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(2)

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
