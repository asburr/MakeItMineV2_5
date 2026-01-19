import os
import json
from pathlib import Path
from typing import Any
from makeitminev2_5.make import Make
from texttable import Texttable


class WSMake(Make):
  """ Workspace work. """

  def _findproject(self,name:str,version:str=None,root:str=None) -> str:
    """ Return path to a project in the workspace.
    :param name: Name of the project.
    :param version: Version of the project.
    :param root: Not used when searching the workspace.
    """
    ws = self.getpreference("ws")
    if not ws: return super()._findproject(name,version)
    with open(ws,"r") as f:
      return self._wsload(json.load(f)).get(name,None)

  def _checkfile(self,file:str) -> str:
    return super()._checkfile(file)

  def _release(self) -> None:
    super()._release()

  def _upversionneeded(self) -> bool:
    return super()._upversionneeded()

  def _upversion(self,version:str,oldversion:str) -> None:
    super()._upversion(version,oldversion)

  def _workTitles(self) -> list:
    return super()._workTitles()

  def _work(self) -> list:
    return super()._work()

  def _work_align(self) -> list:
    return super()._work_align()

  ### End framework required implementations.
 
  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.default_ws = "ws.json"

  def wsset(self,ws:str) -> None:
    """ Select a workspace. Will create the workspace if is does not exist.
    :param ws: path to workspace.
    """
    if not os.path.exists(ws):
      with open(ws,"w") as f: json.dump({},f)
      print(f"info: created {ws}")
    else:
      try:
        with open(ws,"r") as f:
          self._wsload(json.load(f))
      except Exception as e:
        print(f"ERROR: {ws} is not a workspace file or is corrupt, error is {e}")
        os._exit(1)
    self.setpreference(key="ws",value=ws)

  def _getws(self) -> str:
    ws = self.getpreference("ws")
    if not ws:
      print("ERROR: please use wsset to select or create a workspace")
      os._exit(1)
    return ws

  def ws(self) -> None:
    """ Show workspace.
    """
    ws = self._getws()
    with open(ws,"r") as f:
      j = self._wsload(json.load(f))
    if not j:
      print(f"info: {ws} is empty, see wsadd")
      return
    table = Texttable(max_width=os.get_terminal_size().columns)
    titles = ["workspace","project","path"]
    body = [[ws,k,v] for k,v in j.items()]
    table.set_cols_align(["l","l","l"])
    table.add_rows([titles] + body)
    print(table.draw())
    return

  def _wsload(self,j:dict) -> dict:
      return {k:v.replace("${HOME}",str(Path.home())) for k,v in j.items()}

  def _wsdump(self,j:dict) -> dict:
      return {k:v.replace(str(Path.home()),"${HOME}") for k,v in j.items()}

  def wsadd(self,pj:str=None,path:str=None) -> None:
    """ Add project to workspace. Will create the workspace if does not exist.
    :param pj: project name, defaults to current directory.
    :param path: path to the root of the project, defaults to current directory.
    """
    if not path:
      path = self.cwd
    if not os.path.exists(path):
      print(f"ERROR: cannot find project at {path}")
      os._exit(1)
    ws = self._getws()
    with open(ws,"r") as f:
      j = self._wsload(json.load(f))
    if not pj: pj = self.name()
    if pj not in j:
      j[pj] = path
      print(f"info: adding {pj}:{j[pj]}")
      with open(ws,"w") as f: json.dump(self._wsdump(j),f)

  def wsrm(self,pj:str=None) -> None:
    """ Remove project from a workspace.
    :param pj: project name, defaults to current directory.
    """
    ws = self._getws()
    with open(ws,"r") as f: j = self._wsload(json.load(f))
    if not pj:
      pj = next(pj for pj,path in j.items() if path == self.cwd)
      if not pj:
        print(f"ERROR: {self.cwd} not in {ws}")
        os._exit(1)
      print(f"info: removing {pj}")
    if pj not in j:
      print(f"ERROR: {pj} is not in {ws}")
      os._exit(1)
    del j[pj]
    with open(ws,"w") as f: json.dump(self._wsdump(j),f)

  def wswork(self,pj:str=None) -> None:
    """ Work remaining in the workflow for the projects in this workspace.
    :param pj: project name, defaults to current directory.
    """
    ws = self._getws()
    with open(ws,"r") as f: j=self._wsload(json.load(f))
    if not j:
      print(f"ERROR: No projects in {ws}; see wsadd")
      os._exit(1)
    align = self._work_align()
    titles = self._workTitles()
    if len(align) != len(titles):
      print("Error length of title not matching alignment")
      os._exit(1)
    body= []
    for k,v in j.items():
      if pj and k != pj: continue 
      os.chdir(v)
      body.append(self._work())
    (align,t) = self._workreduce(align,titles,body)
    if not t: return
    t = [["name/"+ws]+row for row in t]
    t[0][0] = "workspace"
    align = ["l"] + align
    table = Texttable(max_width=os.get_terminal_size().columns)
    table.set_cols_align(align)
    table.add_rows(t)
    print(table.draw())

  def wsrun(self,cmd:str,pj:str=None,*args:list[Any],**kwargs:dict[Any,Any]) -> any:
    """ Run a command without arguments for all of the projects in the workspace.
    args positional arguments for the command being run.
    kwargs key=value arguments for the command being run.
    :param cmd: command to run over all of the projects in the workspace.
    :param pj: project name, defaults to current directory.
    """
    r = None
    ws = self._getws()
    with open(ws,"r") as f: j=self._wsload(json.load(f))
    if not j:
      print(f"ERROR: No projects in {ws}; see wsadd")
      os._exit(1)
    for k,v in j.items():
      if pj and k != pj: continue 
      os.chdir(v)
      f = getattr(self,cmd,None)
      if not f:
        print(f"ERROR: no such command {cmd}")
        os._exit(1)
      print(f"project:{v}")
      ret = f()
      r = r + ret if r else ret
    return r