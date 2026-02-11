from makeitminev2_5.dkmake import DkMake
from makeitminev2_5.gtmake import GtMake
from makeitminev2_5.pymake import PyMake
from makeitminev2_5.djmake import DJMake
from makeitminev2_5.wsmake import WSMake
from texttable import Texttable
import shutil
import os


class PjMake(DJMake,DkMake,PyMake,GtMake,WSMake):
  """ Project make using other makes. """

  def upversion(self) -> None:
    """ Update version in BUILDVERSION.txt. """
    oldversion = self.version()
    a = oldversion.split(".")
    version =f"{a[0]}.{a[1]}.{int(a[2])+1}"
    name=self.name()
    with open(self.bv,"w") as f:
      f.write(f"{name}:{version}{os.linesep}")
    self._upversion(version,oldversion)

  def release(self,version:str=None,major:int=-1,minor:int=-1) -> None:
    """ Build and test before release. Change the version if provided in the
    parameters, otherwise up version and release only when there are changes. """
    if version or major or minor or self._upversionneeded():
      version=f"{version}.{major}.{minor}"
      self._upversion(version=version,oldversion=self.version())
      self._release()

  def _workwarning(self,pj:str) -> None:
    """ Any warnings. """
    if self.name().lower() != self.name():
      assert not True, f"ERROR: name in {self.bv} must be lowercase"

  def work(self) -> None:
    """ work remaining in the workflow for this project. """
    name = self.name()
    table = Texttable(max_width=shutil.get_terminal_size(fallback=(80, 24)).columns)
    align = self._work_align()
    titles = self._workTitles()
    if len(align) != len(titles):
      assert not True, "Error length of title not matching alignment"
    (align,t) = self._workreduce(align,titles,[self._work()])
    if t:
      align = ["l"] + align
      t = [["project"]+t[0]] + [[name]+t[1]]
    table.set_cols_align(align)
    table.add_rows(t)
    print(table.draw())

  def workflow(self) -> None:
    """ Workflow for this project. """
    name = self.name()
    table = Texttable(max_width=shutil.get_terminal_size(fallback=(80, 24)).columns)
    align = self._work_align()
    titles = self._workTitles()
    if len(align) != len(titles):
      assert not True, "Error length of title not matching alignment"
    align = ["l"] + align
    t = [["project"]+titles] + [[name]+self._work()]
    table.set_cols_align(align)
    table.add_rows(t)
    print(table.draw())

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
