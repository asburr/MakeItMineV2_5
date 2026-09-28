from makeitminev2_5.dkmake import DkMake
from makeitminev2_5.gtmake import GtMake
from makeitminev2_5.pymake import PyMake
from makeitminev2_5.djmake import DJMake
from makeitminev2_5.fkmake import FKMake
from makeitminev2_5.wsmake import WSMake
from makeitminev2_5.make import Make
import os
from makeitminev2_5.makeutils import _MakeUtils


class PjMake(FKMake,DJMake,DkMake,PyMake,GtMake,WSMake,Make):
  """ Project make using other makes. """

  _name = "prj"
  _fullname = "project"
  _active_default = True

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

  def touch(self,p:str,contents:str="") -> None:
    """ Create a file.
      :param p: path to file
      :param contents: contents for file
    """
    if contents:
      with open(p,"w") as f:
        for line in contents.split("\\n"):
          f.write(line+os.linesep)
        return
    self._touch(p)

  def delete(self,p:str) -> None:
    """ Delete a file.
      :param p: path to file
    """
    if os.path.exists(p):
      os.remove(p)

  def setcwd(self,p:str) -> None:
    """ Set the users's shell to change dir to p on login. """
    with open(os.path.join(self.home,".bashrc"),"a") as f:
      f.write(f"cd {p}"+os.linesep)


if __name__ == "__main__":
  PjMake.main()
