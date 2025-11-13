import os
import re
import shutil
from pathlib import Path
from MakeItMineV2_5.make import Make


class PyMake(Make):
  """ Platform independent recipies for a Makefile supporting a Python project.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.python_p = os.path.join("venv","bin","python")
    self.toml = "pyproject.toml"

  def pyproject_dot_toml(self) -> str:
    """ Create pyproject.toml if one does not exists. """
    if os.path.exists(self.toml):
      print(f'{self.toml} exists')
      return
    self.createREADME()
    name = os.path.basename(self.cwd)
    with open(self.toml,"w") as f:
      f.write(f"""
[build-system]
requires = [ "hatchling >= 1.13" ]
build-backend = "hatchling.build"
[project]
name="{name}"
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
[tool.hatch.build.targets.wheel]
packages = ["src/{name}"]
""")

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
      if not self._grep(p,"__version__"):
        with open(p,"a") as f:
          f.write(f'__version__ = "{version}"n')
      else:
        with open(p,"w"):
          f.write(f'''
"""{name}"""
__version__ = "{version}"
''')
    with open(os.path.join("src",name,".__init__version.txt"),"w") as f:
      f.write(f'{self._grep(p,"__version__")}\n')

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
    changes = self._cmd(['git','diff','name-only','origin/main'],show=True)
    if changes:
      self._printChevrons(changes)
      newversion=None
    r = self._cmd(['git','diff','-U0','pyproject.toml'],show=True)
    for l in r.split("n"):
      m = re.search('^+versions=',l)
      if m:
        newversion = version
    if not newversion:
      a = version.split(".")
      newversion =f"{a[0]}.{a[1]}.{int(a[2])+1}"
    # Update files if they are not already updated
    self._sed("pyproject.toml",'version\s*=\s*".*"',f'version = "{newversion}"')
    p = os.path.join("example","release.env")
    if os.path.exists(p):
      self._sed(p,f'IMAGE\s*=\s*{name}:.*',f'IMAGE={name}:{newversion}')
      self._sed(p,f'RELEASE\s*=\s*{name}.*',f'RELEASE={name}:{newversion}')
    p = ".gitlab-ci.yml"
    if os.path.exists(p):
      self._sed(p,'docker_image_version\s*:.*',f'docker_image__version: {newversion}')
    p = "Makefile"
    if os.path.exists(p):
      self._sed(p,f'{name}\s*:[0-9.]*',f'{name}:{newversion}')
    p = os.path.join("docker","Dockerfile")
    if os.path.exists(p):
      self._sed(p,f'{name}==[0-9.]*',f'{name}=={newversion}')
    p = self.projectinit()
    if p:
      self._sed(p,'_version__\s*==\s*[0-9.]*',f'__version__ == {newversion}')
  
  def pybuild(self) -> None:
    """ Build a Python distribution wheel and tar in local dist dir. """
    self._printChevrons(self._cmd([self.python_p,"-m","build",self.cwd],show=True))
  
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
    r = self._cmd(['pip','config','debug'],show=True)
    for l in r.split("\n"):
      if re.search(", exists: ",l): L.append(l)
      if re.search(".index-url",l): I.append(l)
      if re.search(", exists: ",l): T.append(l)
    if not I: print(f"missing index-url in {L}")
    if not T: print(f"missing trusted-host in {L}")
    if not I or not T: raise Exception("error in pypi conf")

  def create_venv(self) -> None:
    """ Python venv """
    self._printChevrons(self._cmd(["python","-m","venv","venv"],show=True))

  def venv_install_from_toml(self) -> None:
    """ Pip install (editable) dependencies from pyproject.toml into venv """
    T=[]
    L=[]
    with open("pyproject.toml","r") as f:
      for l in f:
        if re.search("^test\s*=\s*[",l): T.append(l)
        if re.search("^lint\s*=\s*[",l): L.append(l)
    self.printChevrons(self._cmd([self.python_p,"-m","pip","install","-e",self.cwd],show=True))
    if T:
      self.printChevrons(self._cmd([self.python_p,"-m","pip","install","-e",self.cwd+"[test]"],show=True))
    if L:
      self.printChevrons(self._cmd([self.python_p,"-m","pip","install","-e",self.cwd+"[lint]"],show=True))

  def venv_install_from_req(self) -> None:
    """ Pip install (editable) dependencies from requirements.txt into venv """
    self.printChevrons(self._cmd([self.python_p,"-m","pip","install","-r","requirements.txt"],show=True))

  def requirement_from_venv(self) -> None:
    """ Uses pip freeze to create a requirements.txt from venv. """
    with open("requirements.txt","w") as f:
      for requirement in self._cmd([self.python_p,"-m","pip","freeze"],show=True).split("\n"):
        if requirement.startswith("-e"): continue
        f.write(requirement+"\n")

  def pydownload_from_venv(self) -> None:
    """ Use pip to download packages which creates a local copy of the packages that can be used when creating containers. """
    target="requirements.txt"
    target2=os.path.join("dist",target)
    p = os.path.join("dist","download")
    if not self._rebuild_target(target,[p,target2,"venv"]): return
    self.requirement_from_venv()
    os.makedirs(p,exists_ok=True)
    # ignore means => dont re-download when exists.
    self._cmd([self.python_p,"-m","pip","download","-d",p,"--exists-action","i","-r",target],show=True)
    os.rename(target,target2)   


if __name__ == "__main__":
  PyMake.main()