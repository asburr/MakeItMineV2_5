from makeitminev2_5.dkmake import DkMake
from makeitminev2_5.gtmake import GtMake
from makeitminev2_5.pymake import PyMake
from makeitminev2_5.djmake import DJMake
from makeitminev2_5.wsmake import WSMake
from texttable import Texttable
import shutil
import os


class PjMake(WSMake,GtMake,PyMake,DkMake,DJMake):
  """ Project make using other makes. """

  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return super()._ignorepaths()

  def build(self) -> None:
    """ build """
    self._build()

  def test(self) -> None:
    """ build and test """
    self._build()
    self._test()

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
    self._build()
    self._test()
    if version or major or minor or self._upversionneeded():
      version=f"{version}.{major}.{minor}"
      self._upversion(version=version,oldversion=self.version())
      self._release()

  def _workwarning(self,pj:str) -> None:
    """ Any warnings. """
    if self.name().lower() != self.name():
      print(f"ERROR: name in {self.bv} must be lowercase")
      os._exit(1)

  def _workreduce(self,align:list,titles:list,body:list) -> (list,list):
    """ Remove columns with empty values. """
    showcell=[True for _ in titles]
    for row in body:
      for i,cell in enumerate(row):
        showcell[i] &= (cell != "")
    align = [cell for i,cell in enumerate(align) if showcell[i]]
    t = []
    for row in [titles] + body:
      t.append([cell for i,cell in enumerate(row) if showcell[i]])
    return (align,t)

  def work(self) -> None:
    """ work remaining in the workflow for this project. """
    name = self.name()
    table = Texttable(max_width=shutil.get_terminal_size(fallback=(80, 24)).columns)
    align = self._work_align()
    titles = self._workTitles()
    if len(align) != len(titles):
      print("Error length of title not matching alignment")
      os._exit(1)
    (align,t) = self._workreduce(align,titles,[self._work()])
    if t:
      align = ["l"] + align
      t = [["project"]+t[0]] + [[name]+t[1]]
    table.set_cols_align(align)
    table.add_rows(t)
    print(table.draw())

  def status(self) -> None:
    """ Workflow status for this project. """
    name = self.name()
    table = Texttable(max_width=shutil.get_terminal_size(fallback=(80, 24)).columns)
    align = self._work_align()
    titles = self._workTitles()
    if len(align) != len(titles):
      print("Error length of title not matching alignment")
      os._exit(1)
    align = ["l"] + align
    t = [["project"]+titles] + [[name]+self._work()]
    table.set_cols_align(align)
    table.add_rows(t)
    print(table.draw())


if __name__ == "__main__":
  PjMake.main()