import os
import sys
import re
import argparse
import shutil
from pathlib import Path
import subprocess
import datetime

class Make():
  """ Platform independent recipies for a Makefile supporting a Python project.
  """

  def __init__(self,cwd:str):
    self.cwd = cwd
    self.python_p = os.path.join("venv","bin","python")
    self.__dkinit__(self)

  def __touch(self,p:str) -> None:
    """ util: Touches a file. """
    with open(p,"a"):
      pass

  def __sed(self,fn:str,pattern:str,s:str) -> None:
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

  def __grep(self,fn:str,pattern:str) -> str:
    """ util: Return lines in file that match pattern. """
    retval = []
    with open(fn,"r") as i:
      for l in i:
        if re.search(pattern,l):
          retval.append(l)
    return "\n".join(retval)

  def __cmd(self,cmd:list, show:bool=False) -> str:
    """ util: Non-interactive stdin and stdout, this command captures stdin and stdout. """
    if show: print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise Exception(f"Failed to run {cmd} exit={proc.returncode} stderr={proc.stderr} stdout={proc.stdout}")
    if proc.stderr:
        return proc.stderr + "\n" + proc.stdout
    return proc.stdout

  def __cmdInteractive(self,cmd:list,show:bool=False) -> None:
    """ util: Interactive stdin and stdout, this command outputs to the user and takes input from the user. """
    if show: print(" ".join(cmd))
    subprocess.run(cmd)

  def __printChevrons(self,output:str) -> None:
    """ util: Output is stdout from a command and each line is prepended with >>> before printing. """
    b = output.strip()
    if len(b) == 0: return
    for line in output.strip().split("\n"):
      print(f">>>{line}")

  def __rebuild_target(self,target:str,dependencies: list) -> bool:
    """ util: Check if target needs rebuild based on its dependencies having a newer timestamp. """
    if not os.path.exist(target):
      print(f"{target} does not exist rebuilding")
      return True
    for dependency in dependencies:
      if not os.path.exist(dependency):
        print(f"{dependency} does not existi assuming it will be built when rebuilding {target}")
        return True
      if os.path.getmtime(dependency) > os.path.getmtime(target):
        print(f"{target} is older than {dependency} and needs rebuilding")
        return True
    print(f"{target} is up to date")
    return False

  def pyproject_dot_toml(self) -> str:
    """ Create pyproject.toml if one does not exists. """
    if os.path.exists("pyproject.toml"):
      print('pyproject.toml exists')
      return
    with open("pyproject.toml","w") as f:
      f.write("""
[build-system]
requires = [ "hatchling >= 1.13" ]
build-backend = "hatchling.build"
[project]
name=""
version="0.0.1"
description=""
readme="README.md"

# dependencies for src/
dependencies = [
]
requires-python=">=3.10"

# dependencies for test/
test = [
  build
]
""")

  def projectName(self) -> str:
    """ pyproject.toml; name = "XXX" """
    with open("pyproject.toml","r") as f:
      for l in f:
        m = re.search('^name=\s*=\s*"(.*)"',l)
        if m:
          return m.group(1)

  def projectVersion(self) -> str:
    """ pyproject.toml; version = "XXX" """
    with open("pyproject.toml","r") as f:
      for l in f:
        m = re.search('^version=\s*=\s*"\s*(-9.]*)\s*"',l)
        if m:
          return m.group(1)

  def projectInit(self) -> str:
    """ Find the path to the project's __init__.py that contains __version__.
        There should only be one.
    """
    i = None
    for root, dirs, files in os.walk("src"):
      for file in files:
        if "__init__.py" == file:
          p=os.path.join(root,file)
          with open(p,"r") as f:
            for l in f:
              if re.search('^\s*__version__\s*==',l):
                if i:
                  print(f"Cannot have two __init__.py both with __version__, pelase see {i} and {p}")
                else:
                  i=p
    return i

  def create_Dockerfile(self) -> None:
    """ Create the initial Dockerfile if does not exist. """
    os.makedirs("docker",exist_ok=True)
    p = os.path.join("docker","Dockerfile")
    if os.path.exists(p):
      print(f"{p} exists, wont recreate")
      return
    name = self.projectName()
    if not name:
      print("No name in pyproject.toml, add name=<name> to [project]")
      return
    version=self.projectVersion()
    if not version:
      print("No version in pyproject.toml, add version=0.0.0 to [project]")
      return
    with open(p,"w") as f:
      f.write(f"""
FROM python:3.10
# Install dependencies from local dist directory using temporary mount.
RUN --mount=type=bind,source=./dist,target=/tmp/offline_dist \
    pip install --no-build-isolation --no-index --find-links=/tmp/offline_dist/download -r /tmp/offline_dist/requirements.txt && \
    pip install --no-build-isolation --no-index --find-links=/tmp/offline_dist/download {name}=={version}
""")

  def create_init_dot_py(self) -> None:
    """ Create the init.py with __Version__ used when importing a package i.e. package.__version__.
    """
    name=self.projectName()
    if not name:
      print("No name in pyproject.toml, add name=<name> to [project]")
      return
    version=self.projectVersion()
    if not version:
      print("No version in pyproject.toml, add version=0.0.0 to [project]")
      return
    p=os.path.join("src",name,"__init__.py")
    if os.path.exists(p):
      if not self.__grep(p,"__version__"):
        with open(p,"a") as f:
          f.write(f'__version__ = "{version}"n')
      else:
        with open(p,"w"):
          f.write(f'''
"""{name}"""
__version__ = "{version}"
''')
    with open(os.path.join("src",name,".__init__version.txt"),"w") as f:
      f.write(f'{self.__grep(p,"__version__")}\n')

  def projectversion_update(self) -> str:
    """ One up the project version number if not already one upped.
        TODO; add functionality to update version across multiple projects.
    """
    if not os.path.exists("pyproject.toml"):
      print('No pyproject.toml, please run "make pyproject.toml" to create one')
      return
    name = self.projectname()
    if not name:
      print("No name in pyproject.toml, add 'name=<name>' to [project]")
      return
    version = self.projectVersion()
    if not version:
      print("No version in pyproject.toml, add version=0.0.0 to [project]")
      return
    newversion= version
    changes = self.__cmd(['git','diff','name-only','origin/main'],show=True)
    if changes:
      self.__printChevrons(changes)
      newversion=None
    r = self.__cmd(['git','diff','-U0','pyproject.toml'],show=True)
    for l in r.split("n"):
      m = re.search('^+versions=',l)
      if m:
        newversion = version
    if not newversion:
      a = version.split(".")
      newversion =f"{a[0]}.{a[1]}.{int(a[2])+1}"
    # Update files if they are not already updated
    self.__sed("pyproject.toml",'version\s*=\s*".*"',f'version = "{newversion}"')
    p = os.path.join("example","release.env")
    if os.path.exists(p):
      self.__sed(p,f'IMAGE\s*=\s*{name}:.*',f'IMAGE={name}:{newversion}')
      self.__sed(p,f'RELEASE\s*=\s*{name}.*',f'RELEASE={name}:{newversion}')
    p = ".gitlab-ci.yml"
    if os.path.exists(p):
      self.__sed(p,'docker_image_version\s*:.*',f'docker_image__version: {newversion}')
    p = "Makefile"
    if os.path.exists(p):
      self.__sed(p,f'{name}\s*:[0-9.]*',f'{name}:{newversion}')
    p = os.path.join("docker","Dockerfile")
    if os.path.exists(p):
      self.__sed(p,f'{name}==[0-9.]*',f'{name}=={newversion}')
    p = self.projectinit()
    if p:
      self.__sed(p,'_version__\s*==\s*[0-9.]*',f'__version__ == {newversion}')
  
  def build(self) -> None:
    """ Build a Python distribution wheel and tar in local dist dir. """
    self.__printChevrons(self.__cmd([self.python_p,"-m","build",self.cwd],show=True))
  
  def install_pypki3_conf(self) -> None:
    """ Copy pypki3.conf into the User account. """
    p = os.path.join(Path.home(),".config","pypki3")
    os.makedirs(p,exist_ok=True)
    dst = os.path.join(p,"config.init")
    if os.path.exists(dst):
      print(f"Warning {dst} exists, renaming to {dst}.bak")
      os.rename(dst,dst+".bak")
    # TODO; create config in code.
    print("cp pypki3.conf {dst}")
    shutil.copyfile("pypki3.conf",dst)
  
  def install_pipconf(self) -> None:
    """ Pip config installed for the user account. """
    p=os.path.join(Path.home(),".pip")
    os.makedirs(p,exist_ok=True)
    dst=os.path.join(p,"pip.conf")
    if os.path.exists(dst):
        print(f"Warning {dst} exists, renaming to {dst}.bak")
        os.rename(dst,dst+".bak")
    # TODO; create config in code.
    print(f"cp pip.config {dst}")
  
  def pypi_check(self) -> None:
    """ Pip conf check for urls. """
    L=[]
    I=[]
    T=[]
    r = self.__cmd(['pip','config','debug'],show=True)
    for l in r.split("\n"):
      if re.search(", exists: ",l): L.append(l)
      if re.search(".index-url",l): I.append(l)
      if re.search(", exists: ",l): T.append(l)
    if not I: print(f"missing index-url in {L}")
    if not T: print(f"missing trusted-host in {L}")
    if not I or not T: raise Exception("error in pypi conf")

  def create_venv(self) -> None:
    """ Python venv """
    self.__printChevrons(self.__cmd(["python","-m","venv","venv"],show=True))

  def _dot_dockerignore(self) -> None:
    """
      Overwrite or create .dockerignore to quicken the build process by
      excluding subdirs from the docker context which is used when building containers.
    """
    if not os.path.exists("docker"):
      return
    with open(".dockerignore","w") as f:
      f.write("""
venv/
.git/
__pycache/
download/
""")

  def venv_install_from_toml(self) -> None:
    """ Pip install (editable) dependencies from pyproject.toml into venv """
    T=[]
    L=[]
    with open("pyproject.toml","r") as f:
      for l in f:
        if re.search("^test\s*=\s*[",l): T.append(l)
        if re.search("^lint\s*=\s*[",l): L.append(l)
    self.printChevrons(self.__cmd([self.python_p,"-m","pip","install","-e",self.cwd],show=True))
    if T:
      self.printChevrons(self.__cmd([self.python_p,"-m","pip","install","-e",self.cwd+"[test]"],show=True))
    if L:
      self.printChevrons(self.__cmd([self.python_p,"-m","pip","install","-e",self.cwd+"[lint]"],show=True))

  def venv_install_from_req(self) -> None:
    """ Pip install (editable) dependencies from requirements.txt into venv """
    self.printChevrons(self.__cmd([self.python_p,"-m","pip","install","-r","requirements.txt"],show=True))

  def requirement_from_venv(self) -> None:
    """ Uses pip freeze to create a requirements.txt from venv. """
    with open("requirements.txt","w") as f:
      for requirement in self.__cmd([self.python_p,"-m","pip","freeze"],show=True).split("\n"):
        if requirement.startswith("-e"): continue
        f.write(requirement+"\n")

  def pydownload_from_venv(self) -> None:
    """ Use pip to download packages which creates a local copy of the packages that can be used when creating containers. """
    target="requirements.txt"
    target2=os.path.join("dist",target)
    p = os.path.join("dist","download")
    if not self.__rebuild_target(target,[p,target2,"venv"]): return
    self.requirement_from_venv()
    os.makedirs(p,exists_ok=True)
    # ignore means => dont re-download when exists.
    self.__cmd([self.python_p,"-m","pip","download","-d",p,"--exists-action","i","-r",target],show=True)
    os.rename(target,target2)

  def __dkinit__(self) -> None:
    self.dkf = os.path.join("docker","Dockerfile")
    self.dkdc = os.path.join("example","docker-compose.yml")
    self.dkr = os.path.join("example","release.env")
    self.dkdr = os.path.join("example","dkrun_release.env")

  def dkcheck(self) -> None:
    """ Check if docker is installed """
    if not self._cmd(["which","docker"],show=True):
      print("docker is not installed, please install docker")
      sys.exit(1)

  def dkbuild(self,secret:str) -> None:
    """ Build container using docker/Dockerfile. Optional secret is semicolon separated of id-<id>,src=<path> """
    touchfile=os.path.join("docker","dkbuild")
    if not self.__rebuild_target(touchfile,[self.dkf]): return
    self.dkcheck()
    name = self.projectname()
    version = self.projectversion()
    if secret:
      with open(self.dkf,"r") as f:
        for line in f:
          m = re.search('-mount=type=secret,id=(.*),target='.line)
          if m:
            id = m.group(1)
            if f'id{id}," not in secret':
              print(f"secret {id} is required by {self.dkf}")
              sys.exit(1)
      cmd = ["docker","build"]
      for s in secret.split(";"):
        cmd.append("--secret")
        cmd.append(s)
      cmd += ["--no-cache","-t",f"{name}:{version}","-f",self.dkf,"."]
      self.__cmd(cmd,show=True)
    else:
      self.__cmd(["docker","build","--no-cache","-t",f"{name}:{version}","-f",self.dkf,"."],show=True)
    self.__touch(os.path.join("docker","dkbuild"))

  def __dkrun_release_env(self) -> None:
    with open(self.dkr,"r") as r, open(self.dkdr,"w") as w:
      for line in r:
        if "USERID" in line:
          w.write(f"USERID={os.getuid()}{os.linesep}")
        elif "GROUPID" in line:
          w.write(f"GROUPID={os.getresgid()[0]}{os.linesep}")
        else:
          w.write(line)
    
  def dkrun(self, service:str) -> None:
    """ Run a service in example/docker-compose.yml """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    with open(self.dkdc,"r") as f:
      for line in f:
        if re.search(f"^\s*{service}:",line): break
      for line in f:
        if len(line.strip()) == 0: break
        m = re.search('s*container_name:\s*(.*)',line)
        if m:
          container_name = m.group(1)
          break
    if "container_name" not in locals():
      print(f"Failed to find container_name for {service} in {self.dkdc}")
      return
    self.__dkrun_release_env()
    try:
      self.__cmd(["docker","stop",container_name],show=True)
      self.__cmd(["docker","rm",container_name],show=True)
    except:
      pass
    self.__cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkr,
                           "run","orphans","--name",container_name,"-it",service,"/bin/bash"],show=True)
    self.__cmd(["docker","stop",container_name],show=True)
    self.__cmd(["docker","rm",container_name],show=True)

  def dkpull(self) -> None:
    p = os.path.join("example","docker-compose.yml")
    if not os.path.exists(p):
      print(f"{p} does not exist")
      return
    p2 = os.path.join("example","release.env")
    with open(p2,"r") as f:
      for line in f:
        m = re.search('^PULL_(.*)=(.*)',line)
        if m:
          name = m.group(1)
          image = m.group(2)
          m = re.search(f'^{name}=(.*)',line)
          if not m:
            print(f'{p2} missing {name}=<image>')
            return
          tag = m.group(1)
          if self.__cmd(["docker","images","-q",tag],show=True):
            print(f"Image {tag} already present, wont attemp to repull the remote image")
          else:
            self.__cmd(["docker","pull",image],show=True)
            self.__cmd(["tag",image,tag],show=True)

  def dkup(self) -> None:
    """ Run the services in example/docker-compose.yml """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self.__dkrun_release_env()
    self.__cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "up","--detach"],show=True)

  def dkdown(self) -> None:
    """ Stop the services in docker-compose """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self.__cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "down"],show=True)
    self.__cmd(["docker","network","prune","-f"],show=True)

      