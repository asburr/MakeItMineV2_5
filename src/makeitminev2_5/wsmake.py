import os
import json
from typing import Any
from makeitminev2_5.make import Make
from makeitminev2_5.makeutils import MakeUtils
from texttable import Texttable


class WSMake(Make,MakeUtils):
  """ Workspace work. """

  def _newfile(self,file:str) -> None:
    super().newfile(file)

  def _wsrm(self,ws:str,pj:str,path:str) -> None:
    super()._wsrm(ws,pj,path)

  def _build(self) -> None:
    super()._build()

  def _test(self) -> None:
    super()._test()

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
 
  def __init__(self):
    super().__init__()
    self.default_ws = "ws.json"

  def ws(self,ws:str=None) -> None:
    """ Show workspace. """
    if not ws: ws = self.default_ws
    if os.path.exists(ws):
      with open(ws,"r") as f:
        j = json.load(f)
      if not j:
        print(f"info: {ws} is empty, see wsadd")
        return
      name = self.name()
      table = Texttable(max_width=os.get_terminal_size().columns)
      titles = ["workspace","project","path"]
      body = [[name+"/"+ws,k,v] for k,v in j.items()]
      table.set_cols_align(["l","l","l"])
      table.add_rows([titles] + body)
      print(table.draw())
      return

  def wsadd(self,pj:str=None,path:str=None,ws:str=None) -> None:
    """ Add project to workspace. Will create the workspace if does not exist.
    Optional project name (--pj) and path (--path), defaults to cwd.
    Optional workspace (--ws), defaults to cwd/ws.json"""
    if path and not os.path.exists(path):
      print(f"ERROR: cannot find project path {path}")
      os._exit(1)
    if not ws: ws = self.default_ws
    if not os.path.exists(ws):
      with open(ws,"w") as f: json.dump({},f)
      print(f"info: created {ws}")
      self._newfile(ws)
    with open(ws,"r") as f: j = json.load(f)
    if not pj: pj = self.name()
    if not path:
      path = self.cwd
    if pj not in j:
      j[pj] = path
      print(f"info: adding {pj}:{path}")
      with open(ws,"w") as f: json.dump(j,f)

  def wsrm(self,pj:str=None,ws:str=None) -> None:
    """ Remove project from a workspace. """
    if not ws: ws = self.default_ws
    if not os.path.exists(ws):
      print(f"ERROR: cannot find path {ws}")
      os._exit(1)
    with open(ws,"r") as f: j = json.load(f)
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
    with open(ws,"w") as f: json.dump(j,f)

  def wswork(self,pj:str=None,ws:str=None) -> None:
    """ Work remaining in the workflow for the projects in this workspace. """
    if not ws: ws = self.default_ws
    if not os.path.exists(ws):
      print("ERROR could not find a workspace")
      os._exit(1)
    with open(ws,"r") as f: j=json.load(f)
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

  def wsrun(self,cmd:str,pj:str=None,ws:str=None,*args:list[Any],**kwargs:dict[Any,Any]) -> any:
    """ Run a command without arguments for all of the projects in the workspace.
    ---pj to limit the run to the project named by --pj.
    --ws to specify a workspace named by --ws, ./ws.json is the default.
    args positional arguments for the command being run.
    kwargs key=value arguments for the command being run.
    """
    r = None
    if not ws: ws = self.default_ws
    if not os.path.exists(ws):
      print("ERROR could not find a workspace")
      os._exit(1)
    with open(ws,"r") as f: j=json.load(f)
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

