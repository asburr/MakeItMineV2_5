import os
import re
import argparse
import subprocess
from texttable import Texttable
from pathlib import Path


class Make():
  """ utils for Makes.
  """

  def __init__(self,**kwargs):
    self.cwd = kwargs["cwd"]
    self.home = Path.home()
    self.bv = "BUILD_VERSION.txt"
    self.readme = "README.md"

  def _files(self) -> list:
    """ Perminant files that can be created by this class. """
    return [self.bv,self.readme]

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

  def _cmd(self,cmd:list, show:bool=False, fail:bool=True) -> list:
    """ util: Non-interactive stdin and stdout, this command captures stdin and stdout returning as a list of lines. """
    if show: print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if fail:
          print(f"Failed to run '{' '.join(cmd)}' exit code={proc.returncode}{os.linesep}stderr={proc.stderr}stdout={proc.stdout}")
          os._exit(1)
    e = proc.stderr.strip().split(os.linesep)
    if not e[0]: e=[] # "".split(os.linesep) => ['']
    o = proc.stdout.strip().split(os.linesep)
    if not o[0]: o=[] # "".split(os.linesep) => ['']
    if e and not fail:
        return e + o
    return o

  def _cmdstr(self,cmd:list, show:bool=False, fail:bool=True) -> str:
    """ util: return stdout and stderr as a whole string. """
    return os.linesep.join(self._cmd(cmd,show,fail))

  def _substrin(self,s:str,a:list) -> bool:
    """ Substring in list of strings. """
    return [x for x in a if s in x] != []

  def _cmdInteractive(self,cmd:list,show:bool=False) -> None:
    """ util: Interactive stdin and stdout, this command outputs to the user and takes input from the user. """
    if show: print(" ".join(cmd))
    subprocess.run(cmd)

  def _rebuild_target(self,target:str,dependencies: list) -> bool:
    """ util: Check if target needs rebuild based on its dependencies having a newer timestamp. """
    if not os.path.exist(target):
      print(f"{target} does not exist rebuilding")
      return True
    for dependency in dependencies:
      if not os.path.exist(dependency):
        print(f"{dependency} does not exist assuming it will be built when rebuilding {target}")
        return True
      if os.path.getmtime(dependency) > os.path.getmtime(target):
        print(f"{target} is older than {dependency} and needs rebuilding")
        return True
    print(f"{target} is up to date")
    return False

  def BUILDVERSION_dot_txt(self) -> None:
    """ Create the initial build version file. """
    if not os.path.exists(self.bv):
      name = os.path.basename(self.cwd)
      with open(self.bv,"w") as f:
        f.write(f"{name}:0.0.1{os.linesep}")

  def name(self) -> str:
    """ Get projects name """
    self.BUILDVERSION_dot_txt()
    with open(self.bv,"r") as f:
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(1)

  def version(self) -> str:
    """ Get projects version """
    self.BUILDVERSION_dot_txt()
    with open(self.bv,"r") as f:
      for l in f:
        m = re.search('^(.*):(.*)',l)
        if m:
          return m.group(2)

  def _upversion(self,version:str,oldversion:str) -> None:
    """ Update files containing version from BUILDVERSION.txt. """
    pass

  def upversion(self) -> None:
    """ Increment the project version number """
    oldversion = self.version()
    a = oldversion.split(".")
    version =f"{a[0]}.{a[1]}.{int(a[2])+1}"
    name=self.name()
    with open(self.bv,"w") as f:
      f.write(f"{name}:{version}{os.linesep}")
    self._upversion(version,oldversion)

  def _statusTitles(self) -> list:
    """ Titles for status """
    return []

  def _status(self) -> list:
    """ Gather project status """
    return []
  
  def _statuswarning(self) -> list:
    """ Any warnings. """
    return []

  def _status_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return []  

  def status(self) -> None:
    """ Status of the project. """
    table = Texttable(max_width=os.get_terminal_size().columns)
    align = self._status_align()
    titles = self._statusTitles()
    for warning in self._statuswarning():
      print(warning)
    body = self._status()
    if len(align) != len(titles):
      print("Error length of title not matching alignment")
      os._exit(1)
    table.set_cols_align(align)
    table.add_rows([titles]+[body])
    print(table.draw())

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters.
    super()._main(ap)
    ap.add_argument('-s', '--service', help="Service for docker dkrun")
    cls.command_parameters["dkrun"] = ["service"]
    ap.add_argument('-S', '--secrets', help="zero, one or more secrets for docker dkbuild")
    cls.command_parameters_optional["dkbuild"] = ["secrets"]
    """
    cls.command_parameters={} # [cmd]=list(param:str)
    cls.command_parameters_optional={} # [cmd]=list(param:str)

  @classmethod
  def genmakefile(cls,d:dict):
    """ Generate a Makefile to invoke MakeItMine. """
    with open("Makefile","w") as f:
      f.write("""
ifeq ($(MIM),)
  $(error $$MIM must be defined as the path to the MakeItMine project)
endif
MAKE:=$(MIM)/venv/bin/python -m MakeItMineV2_5.pjmake\n\n
""")
      for k,v in d.items():
        f.write(k+":\n")
        f.write(f"\t$(MAKE) {k}\n\n")

  @classmethod
  def main(cls):
    p = argparse.ArgumentParser(description="",
                                formatter_class=argparse.RawTextHelpFormatter)
    m = cls(cwd=os.getcwd())
    d = {x.replace("_dot_","."):x+":"+(getattr(m,x).__doc__.strip() if getattr(m,x).__doc__ else "?") 
         for x in dir(cls) if not x.startswith("_") and x !="main"
         and not x.startswith("__Makefile__")}
    d["genmakefile"] = cls.genmakefile.__doc__
    p.add_argument('command', choices=d.keys(), help=os.linesep.join(d.values()))
    cls._main(p)
    a = p.parse_args()
    if a.command == "genmakefile":
      cls.genmakefile(d)
      return
    params = {}
    if a.command in cls.command_parameters:
      for param in cls.command_parameters[a.command]:
        params[param] = getattr(a,param,None)
        if not params[param]:
          print(f"{a.command} missing --{param}")
          return
    if a.command in cls.command_parameters_optional:
      for param in cls.command_parameters_optional[a.command]:
        params[param] = getattr(a,param,None)
    r = getattr(m,a.command)(**params)
    if r is not None: print(r)


if __name__ == "__main__":
  Make.main()