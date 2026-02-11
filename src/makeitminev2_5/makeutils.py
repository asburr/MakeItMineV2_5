import os
import re
from pathlib import Path
import subprocess


class MakeUtils():
  """ Utils """
  my_env = os.environ.copy()
  my_env["PYTHONUNBUFFERED"] = "1"

  def __init__(self,**kwargs):
    self.cwd = os.getcwd()
    self.home = Path.home()

  @classmethod
  def _touch(cls,p:str) -> None:
    """ util: Touches a file. """
    Path(p).touch()

  @classmethod
  def _sed(cls,fn:str,pattern:str,s:str) -> None:
    """ Util: Change pattern to s if s not already in line that matches pattern. """
    changed=False
    hfn = os.path.join(os.path.dirname(fn),f".{os.path.basename(fn)}")
    with open(fn,"r") as i:
      with open(hfn,"w") as o:
        for line in i:
          nl = re.sub(pattern,s,line)
          o.write(nl)
          if line != nl:
            if not changed:
              print(f"sed 's/{pattern}/{s}/g' {fn}")
              changed=True
            print(f">>>{nl}")
    if not changed:
      os.remove(hfn)
    else:
      os.rename(hfn,fn)

  @classmethod
  def _grep(cls,fn:str,pattern:str) -> str:
    """ util: Return lines in file that match pattern. """
    retval = []
    with open(fn,"r") as i:
      for line in i:
        if re.search(pattern,line):
          retval.append(line)
    return "\n".join(retval)

  @classmethod
  def _grep_match(cls,fn:str,pattern:str) -> re.Match:
    """ util: Yield Match for each line in file that matches pattern. """
    with open(fn,"r") as i:
      for line in i:
        m = re.match(pattern,line)
        if m: yield m

  @classmethod
  def _append(cls,fn:str,line:str) -> None:
    """ util: append line to file. """
    with open(fn,"a") as f:
      f.write(line+os.linesep)

  @classmethod
  def _cmd(cls,cmd:list, _show:bool=False, fail:bool=True,stderr:bool=False) -> list:
    """ util: Non-interactive stdin and stdout, this command captures stdin and stdout returning as a list of lines. """
    if _show: print(" ".join(cmd))
    proc = subprocess.run(cmd, env=cls.my_env, capture_output=True, text=True)
    if proc.returncode != 0:
        assert not True, f"Failed to run '{' '.join(cmd)}' exit code={proc.returncode}{os.linesep} stderr={proc.stderr}stdout={proc.stdout}"
    e = proc.stderr.strip()
    e = e.split(os.linesep) if e else []
    o = proc.stdout.strip()
    o = o.split(os.linesep) if o else []
    if e and stderr:
        return e + o
    return o

  @classmethod
  def _cmdstr(cls,cmd:list, _show:bool=False, fail:bool=True,stderr:bool=False) -> str:
    """ util: return stdout and stderr as a whole string. """
    a=cls._cmd(cmd,_show,fail,stderr)
    if len(a): return os.linesep.join(a)
    return None

  @classmethod
  def _substring(cls,s:str,a:list) -> bool:
    """ Substring in list of strings. """
    return [x for x in a if s in x] != []

  @classmethod
  def _cmdInteractive(cls,cmd:list,fail:bool=True,_show:bool=False) -> None:
    """ util: Interactive stdin and stdout, this command outputs to the user and takes input from the user. """
    if _show: print(" ".join(cmd))
    proc = subprocess.run(cmd, env=cls.my_env)
    if proc.returncode != 0:
        assert not True, f"Failed to run '{' '.join(cmd)}' exit code={proc.returncode}{os.linesep} stderr={proc.stderr}stdout={proc.stdout}"

  @classmethod
  def _newermtime(cls,mtime:float,p:str) -> str:
    """ anything in p including subdirs that is newer than target """
    t = os.path.getmtime(p)
    if t > mtime:
      return p
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
          lst = [x for x in files if os.path.getmtime(os.path.join(root,x)) > mtime]
          if lst: return os.path.join(root,lst[0])
          for dir in dirs:
            p = os.path.join(root,dir)
            if cls._newermtime(mtime,p):
              return p
    return None

  @classmethod
  def _rebuild_target(cls,target:str,dependencies: list,msg:bool=True) -> str:
    """ util: Check if target needs rebuild based on its dependencies having a newer timestamp. """
    if not os.path.exists(target):
      if msg: print(f"target '{target}' does not exist rebuilding")
      return target
    mtime = os.path.getmtime(target)
    for dependency in dependencies:
      if not os.path.exists(dependency):
        if msg: print(f"target '{target}' is out of date, dependency '{dependency}' does not exist assuming it will be built when rebuilding target.")
        return dependency
      p = cls._newermtime(mtime,dependency)
      if p:
        if msg: print(f"target '{target}' is out of date, dependency '{dependency}' is older than dependency and needs rebuilding")
        return p
    if msg: print(f'target "{target}" is up to date, dependencies are {",".join(dependencies)}')
    return None

  @classmethod
  def _workreduce(cls,align:list,titles:list,body:list) -> (list,list):
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

  def _setcwdX(self,pj:str=None) -> None:
    """ Util: change dir to pj or cwd """
    os.chdir(pj if pj else self.cwd)
