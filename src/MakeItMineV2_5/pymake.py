import os
import re
import argparse
from MakeItMineV2_5.make import Make


class PyMake(Make):
  """ Platform independent recipies for a Makefile supporting a Python project.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.python_p = os.path.join("venv","bin","python")
    self.toml = "pyproject.toml"
    self.download = os.path.join(self.home,".make_download")
    self.devreq = "dev_requirements.txt"
    self.prodreq = "prod_requirements.txt"

  def _files(self) -> list:
    """ Perminant files that can be created by this class. """
    return super()._files()+[self.toml,self.devreq,self.prodreq]

  def project_dot_toml(self) -> str:
    """ Create pyproject.toml if one does not exists. """
    if os.path.exists(self.toml):
      print(f'{self.toml} exists')
      return
    self.README_dot_txt()
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

  def pyinit_dot_py_path(self) -> str:
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

  def init_dot_py(self) -> None:
    """ Create the init.py with __version__ used when importing a package i.e. package.__version__.
    """
    name=self.name()
    version=self.projectVersion()
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

  def pyversion(self,packagename:str,show=True) -> str:
    """ Return version of a package from the project of the same name in the workspace. """
    python_p = os.path.abspath(os.path.join("..",packagename,"venv","bin","python"))
    if not os.path.exists(python_p):
      print(f"{python_p} not exists")
      os._exit(1)
    for line in self._cmd([python_p,"-m","pip","show",packagename],show=show).split(os.linesep):
      m = re.search('^Version: (.*)',line)
      if m:
        return m.group(1)

  def _upversion(self,version:str,oldversion:str) -> str:
    """ Update files with the build version. """
    self._sed(self.toml,'version\s*=\s*".*"',f'version = "{version}"')
    p = self.pyinit_dot_py_path()
    if p:
      self._sed(p,'_version__\s*==\s*[0-9.]*',f'__version__ == {version}')

  def pybuild(self) -> None:
    """ Build a Python distribution wheel and tar in local dist dir. """
    self.pyrequirements()
    # ignore means => dont re-download when exists.
    self._cmd([self.python_p,"-m","pip","download","-d",self.download,"--exists-action","i","-r",self.prodreq],show=True)
    self._cmd([self.python_p,"-m","build","--no-index","--find-links",self.download,self.cwd],show=True)

  def pycheck(self) -> None:
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

  def venv(self) -> None:
    """ Python venv with dependencies from dev_requirements.txt and then editable from pyproject.toml.
        Using downloaded packages, or whatever pypi is configured by the user.
    """
    self._cmdInteractive(["python","-m","venv","venv"],show=True)
    if os.path.exists(self.devreq):
      self._cmdInteractive([self.python_p,"-m","pip","install","--find-links",self.download,"-r",self.devreq],show=True)
    if os.path.exists(self.toml):
      o = []
      if self._grep(self.toml,"^test\s*=\s*\["): o.append("test")
      if self._grep(self.toml,"^lint\s*=\s*\["): o.append("lint")
      if o:
        self._cmdInteractive([self.python_p,"-m","pip","install","--find-links",self.download,"-e",self.cwd+f"[{','.join(o)}]"],show=True)
      else:
        self._cmdInteractive([self.python_p,"-m","pip","install","--find-links",self.download,"-e",self.cwd],show=True)

  def prod_venv(self) -> None:
    """ Python venv with dependencies from prod_requirements.txt and then from pyproject.toml.
        Using downloaded packages only.
    """
    self._cmd(["python","-m","venv","venv"],show=True)
    if os.path.exists(self.prodreq):
      self._cmdInteractive([self.python_p,"-m","pip","install","--no-index","--find-links",self.download,"-r",self.prodreq],show=True)
    if os.path.exists(self.toml):
      self._cmdInteractive([self.python_p,"-m","pip","install","--no-index","--find-links",self.download,self.cwd],show=True)

  def pyrequirements(self) -> None:
    """ Uses pip freeze to create a requirements.txt and workspace_requirements.txt from venv. """
    with open(self.devreq,"w") as dev, open(self.prodreq,"w") as prod:
      for requirement in self._cmd([self.python_p,"-m","pip","freeze"],show=True).split("\n"):
        if requirement.startswith("-e"):
          m = re.search("#egg=(.*)",requirement)
          if m:
            dev.write("-e "+os.path.abspath(os.path.join("..",m.group(1)))+os.linesep) # Project installed editable assumed to be in the same workspace.
            prod.write(requirement+"=="+self.pyversion(requirement,show=False)+os.linesep)
        else:
          dev.write(requirement+os.linesep)
          prod.write(requirement+os.linesep)

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters. """
    super()._main(ap)
    ap.add_argument('-p', '--packagename', help="Name of the package for pyversion")
    cls.command_parameters["pyversion"] = ["packagename"]


if __name__ == "__main__":
  PyMake.main()