import os
import re
from pathlib import Path
import subprocess


class MakeUtils():
  """ Utils """

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

  def _cmd(self,cmd:list, _show:bool=False, fail:bool=True,stderr:bool=False) -> list:
    """ util: Non-interactive stdin and stdout, this command captures stdin and stdout returning as a list of lines. """
    if _show: print(" ".join(cmd))
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

  def _cmdstr(self,cmd:list, _show:bool=False, fail:bool=True) -> str:
    """ util: return stdout and stderr as a whole string. """
    a=self._cmd(cmd,_show,fail)
    if len(a): return os.linesep.join(a)
    return None

  def _substrin(self,s:str,a:list) -> bool:
    """ Substring in list of strings. """
    return [x for x in a if s in x] != []

  def _cmdInteractive(self,cmd:list,_show:bool=False) -> None:
    """ util: Interactive stdin and stdout, this command outputs to the user and takes input from the user. """
    if _show: print(" ".join(cmd))
    subprocess.run(cmd)

  def _newermtime(self,mtime:float,p:str) -> bool:
    """ anything in p including subdirs that is newer than target """
    if os.path.getmtime(p) > mtime:
      return True
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
          if [x for x in files if os.path.getmtime(os.path.join(root,x)) > mtime]:
            return True
          for dir in dirs:
            if self._newermtime(mtime,os.path.join(root,dir)):
              return True
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

  def __init__(self):
    self.cwd = os.getcwd()
    self.home = Path.home()
    self.bv = "BUILD_VERSION.txt"
    self.readme = "README.md"

  def _setcwdX(self,pj:str=None) -> None:
    """ Util: change dir to pj or cwd """
    os.chdir(pj if pj else self.cwd)