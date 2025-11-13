import os
import sys
import re
import argparse
from MakeItMineV2_5.make import Make


class DkMake(Make):
  """ Platform independent recipies for a Makefile supporting a Docker projects.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.dkf = os.path.join("docker","Dockerfile")
    self.dkdc = os.path.join("example","docker-compose.yml")
    self.dkr = os.path.join("example","release.env")
    self.dkdr = os.path.join("example","dkrun_release.env")

  def files(self) -> list:
    return super().files() + [self.dkf,self.dkdc,self.dkr,self.dkdr]

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

  def dkcheck(self) -> None:
    """ Check if docker is installed """
    if not self._cmd(["which","docker"],show=True):
      print("docker is not installed, please install docker")
      sys.exit(1)

  def dkbuild(self,secret:str) -> None:
    """ Build container using docker/Dockerfile. Optional secret is semicolon separated of id-<id>,src=<path> """
    touchfile=os.path.join("docker","dkbuild")
    if not self._rebuild_target(touchfile,[self.dkf]): return
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
      self._cmd(cmd,show=True)
    else:
      self._cmd(["docker","build","--no-cache","-t",f"{name}:{version}","-f",self.dkf,"."],show=True)
    self._touch(os.path.join("docker","dkbuild"))

  def _run_release_env(self) -> None:
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
    self._dkrun_release_env()
    try:
      self._cmd(["docker","stop",container_name],show=True)
      self._cmd(["docker","rm",container_name],show=True)
    except:
      pass
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkr,
                           "run","orphans","--name",container_name,"-it",service,"/bin/bash"],show=True)
    self._cmd(["docker","stop",container_name],show=True)
    self._cmd(["docker","rm",container_name],show=True)

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
          if self._cmd(["docker","images","-q",tag],show=True):
            print(f"Image {tag} already present, wont attemp to repull the remote image")
          else:
            self._cmd(["docker","pull",image],show=True)
            self._cmd(["tag",image,tag],show=True)

  def dkup(self) -> None:
    """ Run the services in example/docker-compose.yml """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env()
    self._cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "up","--detach"],show=True)

  def dkdown(self) -> None:
    """ Stop the services in docker-compose """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "down"],show=True)
    self._cmd(["docker","network","prune","-f"],show=True)

  def _dkprodimage(self) -> bool:
    """ Check if the docker production image exists """
    name = self.name()
    version = self.version()
    if self._cmd(["docker","images","-q",f"{name}:{version}"]):
      return True
    else:
      return False

  def _dkdevimage(self) -> bool:
    """ Check if the docker production image exists """
    name = self.name()
    version = self.version()
    if self._cmd(["docker","images","-q",f"{name}_editable:{version}"]):
      return True
    else:
      return False

  def _showTitles(self) -> list:
    """ Titles for show """
    return super()._showTitles()+["branch","remote"]

  def _show(self) -> list:
    """ Gather project status """
    return super()._show()+[f"{self.gtlocalbranch()}",f"sid dd:mm"]

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters. """
    super()._main(ap)
    ap.add_argument('-s', '--service', help="Service for docker dkrun")
    cls.command_parameters["dkrun"] = ["service"]
    ap.add_argument('-S', '--secrets', help="zero, one or more secrets for docker dkbuild")
    cls.command_parameters_optional["dkbuild"] = ["secrets"]


if __name__ == "__main__":
  DkMake.main()