import os
import re
import argparse
import subprocess
import json
from texttable import Texttable
from pathlib import Path


class Make():
  """ Workflow template for making a software project. """

  def name(self,pj:str=None) -> str:
    """ Get project name """
    self.BUILDVERSION_dot_txt(pj)
    p=os.path.join(pj if pj else self.cwd,self.bv)
    with open(p,"r") as f:
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(1)

  def version(self,pj:str=None) -> str:
    """ Get projects version """
    self.BUILDVERSION_dot_txt(pj)
    p=os.path.join(pj if pj else self.cwd,self.bv)
    with open(p,"r") as f:
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(2)

  def workspace(self,ws:str,add:str,remove:str) -> None:
    """ Add or remove project from a workspace. """
    if add:
      if not os.path.exists(add):
        print(f"ERROR: cannot find path {add}")
        os._exit(1)
    if not os.path.exists(ws):
      print(f"ERROR: cannot find path {ws}")
      os._exit(1)
    p = os.path.join(ws,"ws.json")
    if not os.path.exists(p):
      with open(p,"w") as f: f.write("[]")
    with open(p,"r") as f: j = json.load(f)
    if add:
      if add not in j: j.append(add)
    if remove in j: j.remove(remove)
    with open(p,"w") as f: json.dump(j,f)

  def _run(self,cmd,pj:str=None,ws:str=None) -> any:
    """ Run a command for projects in workspace and individual project. """
    r = None
    if pj:
      os.chdir(pj)
      r = cmd(pj)
    if ws:
      with open(ws,"r") as f: j=json.load(f)
      for pj in j:
        os.chdir(pj)
        rv = cmd(pj)
        if rv:
          if r: r += rv
          else: r = rv
    if not pj and not ws:
      os.chdir(self.cwd)
      r = cmd()
    return r

  def _build(self,pj:str) -> None:
    """ build the project. """
    pass

  def build(self,pj:str=None,ws:str=None) -> None:
    """ build """
    self._run(self._build,pj,ws)

  def _test(self,pj:str) -> None:
    """ test """
    pass

  def test(self,pj:str=None,ws:str=None) -> None:
    """ build and test """
    self._run(self._build,pj,ws)
    self._run(self._test,pj,ws)

  def _upversionneeded(self,version:str,oldversion:str) -> bool:
    """ Is up version needed. """
    return False

  def _upversion(self,pj:str,version:str,oldversion:str) -> None:
    """ Update version in BUILDVERSION.txt. """
    oldversion = self.version(pj)
    a = oldversion.split(".")
    version =f"{a[0]}.{a[1]}.{int(a[2])+1}"
    name=self.name()
    with open(self.bv,"w") as f:
      f.write(f"{name}:{version}{os.linesep}")
    self._upversion(version,oldversion)

  def upversion(self,pj:str=None,ws:str=None) -> None:
    """ upversion """
    self._run(self._upversion,pj,ws)

  def _changes(self,pj:str) -> bool:
    """ Any changes to the project. """
    return False

  def _release(self,pj:str) -> None:
    """ Build and test and release """
    self._build(pj)
    self._test(pj)
    if self._changes(pj): self._upversion(pj)
    self._release(pj)

  def release(self,pj:str=None,ws:str=None) -> None:
    """ release """
    self._run(self._release,pj,ws)

  def _statusTitles(self) -> list:
    """ Titles for status """
    return []

  def _status(self) -> list:
    """ Gather project status """
    return []

  def _statuswarning(self,pj:str) -> None:
    """ Any warnings. """
    if self.name().lower() != self.name():
      print(f"ERROR: name in {self.bv} must be lowercase")
      os._exit(1)

  def _status_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return []  

  def status(self,pj:str=None,ws:str=None) -> None:
    """ Status of the project. """
    table = Texttable(max_width=os.get_terminal_size().columns)
    align = self._status_align()
    titles = self._statusTitles()
    if len(align) != len(titles):
      print("Error length of title not matching alignment")
      os._exit(1)
    table.set_cols_align(align)
    if titles:
      table.add_rows([titles] + [self._run(self._status,pj,ws)])
      print(table.draw())

  def __init__(self,**kwargs):
    self.cwd = kwargs["cwd"]
    self.home = Path.home()
    self.bv = "BUILD_VERSION.txt"
    self.readme = "README.md"

  def _files(self) -> list:
    """ Perminant files that can be created by this class. """
    return [self.bv,self.readme]

  def _setcwd(self,pj:str=None) -> None:
    """ Util: change dir to pj or cwd """
    os.chdir(pj if pj else self.cwd)

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

  def _touch(self,p:str) -> None:
    """ util: Touches a file. """
    with open(p,"a"):
      pass

  def _sed(self,fn:str,pattern:str,s:str) -> None:
    """ Util: Change pattern to s if s not already in line that matches pattern. """
    changed=False
    hfn = os.path.join(os.path.dirname(fn),f".{os.path.basename(fn)}")
    with open(fn,"r") as i:
      with open(hfn,"w") as o:
        for l in i:
          nl = re.sub(pattern,s,l)
          o.write(nl)
          if l != nl:
            if not changed:
              print(f"sed 's/{pattern}/{s}/g' {fn}")
              changed=True
            print(f">>>{nl}")
    if not changed:
      os.remove(hfn)
    else:
      os.rename(hfn,fn)

  def _grep(self,fn:str,pattern:str) -> str:
    """ util: Return lines in file that match pattern. """
    retval = []
    with open(fn,"r") as i:
      for l in i:
        if re.search(pattern,l):
          retval.append(l)
    return "\n".join(retval)

  def _append(self,fn:str,line:str) -> None:
    """ util: append line to file. """
    with open(fn,"a") as f:
      f.write(line+os.linesep)

  def _cmd(self,cmd:list, show:bool=False, fail:bool=True,stderr:bool=False) -> list:
    """ util: Non-interactive stdin and stdout, this command captures stdin and stdout returning as a list of lines. """
    if show: print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if fail:
          print(f"Failed to run '{' '.join(cmd)}' exit code={proc.returncode}{os.linesep} stderr={proc.stderr}stdout={proc.stdout}")
          os._exit(1)
    e = proc.stderr.strip().split(os.linesep)
    if not e[0]: e=[] # "".split(os.linesep) => ['']
    o = proc.stdout.strip().split(os.linesep)
    if not o[0]: o=[] # "".split(os.linesep) => ['']
    if e and stderr:
        return e + o
    return o

  def _cmdstr(self,cmd:list, show:bool=False, fail:bool=True) -> str:
    """ util: return stdout and stderr as a whole string. """
    a=self._cmd(cmd,show,fail)
    if len(a): return os.linesep.join(a)
    return None

  def _substrin(self,s:str,a:list) -> bool:
    """ Substring in list of strings. """
    return [x for x in a if s in x] != []

  def _cmdInteractive(self,cmd:list,show:bool=False) -> None:
    """ util: Interactive stdin and stdout, this command outputs to the user and takes input from the user. """
    if show: print(" ".join(cmd))
    subprocess.run(cmd)

  def _newermtime(self,mtime:float,p:str) -> bool:
    """ anything in p including subdirs that is newer than target """
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
          if [x for x in files if os.path.getmtime(os.path.join(root,x)) > mtime]:
            return True
          for dir in dirs:
            if self._newermtime(mtime,dir): return True
    else:
      if os.path.getmtime(p) > mtime: return True
    return False

  def _rebuild_target(self,target:str,dependencies: list) -> bool:
    """ util: Check if target needs rebuild based on its dependencies having a newer timestamp. """
    if not os.path.exists(target):
      print(f"{target} does not exist rebuilding")
      return True
    mtime = os.path.getmtime(target)
    for dependency in dependencies:
      if not os.path.exists(dependency):
        # Dependency does not exist assuming it will be built when rebuilding target.
        return True
      if self._newermtime(mtime,dependency):
        # target is older than dependency and needs rebuilding
        return True
    # target is up to date
    return False

  def BUILDVERSION_dot_txt(self,p:str=None) -> None:
    """ Create the initial build version file. """
    p=os.path.join(p if p else self.cwd,self.bv)
    if not os.path.exists(p):
      name = os.path.basename(os.path.dirname(p))
      with open(p,"w") as f:
        f.write(f"{name}:0.0.1{os.linesep}")

  @classmethod
  def _add_argument(cls,ap:argparse.ArgumentParser,option:str,help:str,cmds:list,optional:bool=False) -> None:
    """ option is added to cmd, all cmds if cmd in None, optional if optional is True. """
    if f'--{option}' not in ap._option_string_actions:
      ap.add_argument(f"--{option}",help=help)
    for cmd in cmds:
      if optional:
        cls.command_parameters_optional.setdefault(cmd,[]).append(option)
      else:
        cls.command_parameters.setdefault(cmd,[]).append(option)

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters.
    super()._main(ap)
    self._add_argument(ap, '--service', help="Service for docker dkrun",cmds=["dkrun"])
    self._add_argument(ap, 'secrets', help="zero, one or more secrets for docker dkbuild", cmds=["dkbuild"])
    """
    cls.command_parameters={} # [cmd]=list(param:str)
    cls.command_parameters_optional={} # [cmd]=list(param:str)
    cls._add_argument(ap, 'ws',
                      help="Path to root of the workspace",
                      cmds=["workspace"])
    cls._add_argument(ap, 'add',
                      help="Add project path to workspace",
                      cmds=["workspace"],optional=True)
    cls._add_argument(ap, 'remove',
                      help="Remove project path from workspace",
                      cmds=["workspace"],optional=True)
    cls._add_argument(ap, 'ws',
                      help="Path to root of the workspace, default is no workspace",
                      cmds=["build","test","done","release","status"],
                      optional=True)
    cls._add_argument(ap, "pj",
                      help="Path to root of the project, default to cwd",
                      cmds=["build","test","done","release","status"],
                      optional=True)

  @classmethod
  def main(cls):
    p = argparse.ArgumentParser(description="",
                                formatter_class=argparse.RawTextHelpFormatter)
    m = cls(cwd=os.getcwd())
    d = {x.replace("_dot_","."):x+":"+(getattr(m,x).__doc__.strip() if getattr(m,x).__doc__ else "?") 
         for x in dir(cls) if not x.startswith("_") and x !="main"
         and not x.startswith("__Makefile__")}
    p.add_argument('command', choices=d.keys(), help=os.linesep.join(d.values()))
    cls._main(p)
    a = p.parse_args()
    params = {}
    for param in (cls.command_parameters.get(a.command,[]) +
                  cls.command_parameters.get(None,[])):
      params[param] = getattr(a,param,None)
      if not params[param]:
        print(f"{a.command} missing --{param}")
        return
    for param in (cls.command_parameters_optional.get(a.command,[]) +
                  cls.command_parameters_optional.get(None,[])):
      params[param] = getattr(a,param,None)
    r = getattr(m,a.command)(**params)
    if r is not None: print(r)


if __name__ == "__main__":
  Make.main()