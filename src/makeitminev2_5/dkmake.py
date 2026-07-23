import os
import sys
import re
from makeitminev2_5.abc_make import _ABCMake


class DkMake(_ABCMake):
  """ Platform independent recipies for a Makefile supporting a Docker projects.
  """
  _name = "dk"
  _fullname = "docker and compose"
  _active_default = False

  def _checkfile(self,file:str) -> bool:
    if file == "Dockerfile":
      return self.dkbuild(check=True)
    if os.path.basename(file) == "Dockerfile":
      self._cmd(["docker","build","--check",os.path.dirname(file)],
                fail=True,_show=True,stderr=True)
    return super()._checkfile(file)

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.dkf = os.path.join("docker","Dockerfile")
    self.dkdc = "compose.yaml"
    self.dkr = "release.env"
    self.dkdr = "dkrun_release.env"

  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return super()._ignorepaths() + [self.dkdr]

  def _create_files(self):
    self._setpreference(self._name,True)
    self.create_Dockerfile()
    self._dot_dockerignore()

  def create_Dockerfile(self) -> None:
    """ Create the initial Dockerfile if does not exist. """
    os.makedirs("docker",exist_ok=True)
    p = os.path.join("docker","Dockerfile")
    if os.path.exists(p):
      print(f"{p} exists, wont recreate")
      return
    name = self.name()
    if not name:
      print("No name in pyproject.toml, add name=<name> to [project]")
      return
    version=self.version()
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

  def dkcheck(self,_show:bool=True) -> None:
    """ Check if docker is installed """
    if not self._cmd(["which","docker"],_show=_show):
      print("docker is not installed. apt update; apt-get install docker.io; sudo usermod -aG docker ${USER}")
      sys.exit(1)
    if "docker" not in self._cmdstr(["groups"],_show=_show):
      print("user is not in the docker group. sudo usermod -aG docker ${USER}; login again!!")
      sys.exit(1)
    r = self._cmdstr(["docker","buildx","version"],fail=False,_show=_show,stderr=True)
    if "unknown command" in r:
      print("docker buildx is not installed. sudo apt-get install docker-buildx")
      sys.exit(1)
    if not self._cmd(["docker","compose"],_show=_show):
      print("docker compose is not installed. apt update; apt-get install docker-compose-plugin")
      print("""
Hint:

1 Update your package index and install prerequisites:  
  sudo apt-get update
  sudo apt-get install ca-certificates curl gnupg
2 Add Docker’s official GPG key:
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
3 Set up the repository:
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
4 Install the Compose Plugin:
  sudo apt-get update
  sudo apt-get install docker-compose-plugin
""")
      print("Note: must 'Add Docker’s official GPG key' and 'Set up the repository' before installing the plugin")
      sys.exit(1)

  def dkbuild(self,buildargk:list[str]=[],buildargv:list[str]=[],secret:str=None,check:bool=False,force:bool=False) -> None:
    """ Build container using docker/Dockerfile.
      :param buildargk: Keys for build-arg.
      :param buildargv: Values for build-arg.
      :param secret: semicolon separated of id=<id>,src=<path>.
      :param check: checks the Dockerfile and does not build anything.
    """
    touchfile=os.path.join("docker",".dkbuild.touch")
    dependencies = [self.dkf]
    # Scan dockerfile for additional dependencies.
    for m in self._grep_match(self.dkf,"#\s*MIM:\s*rebuild_target:\s*(.*)\s*=\s*(.*)"):
      if m.group(1) == "dockerfile": dependencies.append(m.group(2))
    if not check and not force and not self._rebuild_target(touchfile,dependencies): return
    self.dkcheck()
    name = self.name()
    version = self.version()
    cmd = ["docker","build"]
    if check: cmd += ["--check"]
    with open(self.dkf,"r") as f:
      for line in f:
        m = re.search('--mount=type=secret,id=(.*),target=',line)
        if m:
          id = m.group(1)
          if not secret or f"id={id}," not in secret:
            m = f"ERROR, expecting: --secret id={id},src=<path> - see {self.dkf}"
            if check: return m
            print(m);
            sys.exit(1)
        m = re.search('^ARG ([^= #]*).*',line)
        if m:
          k = m.group(1).strip()
          if k in ["UID","GID"]: continue
          m = re.search('.*:python (.*):.*',line)
          if m:
            # exec support muiltiple statments and returns nothing but must set x for "or x" to work.
            p = m.group(1).strip()
            results = {}
            v= exec(p, globals(), results)
            v = results.get("x")
            if v is None:
              m = f"ERROR in {self.dkf} in python: {p}"
              if check: return m
              assert not True, m
            cmd.append("--build-arg"); cmd.append(f"{k}={v}")
          elif not re.match(".*=.*",line):
            if k not in buildargk:
              m = f"ERROR, expecting: --buildargk {k} --buildargv <value> {line}"
              if check: return m
              assert not True, m
    for k,v in zip(buildargk,buildargv):
      cmd.append("--build-arg"); cmd.append(f"{k}={v}")
    if secret:
      for s in secret.split(";"):
        cmd.append("--secret"); cmd.append(s)
    cmd += ["-f",self.dkf]
    if check:
      r = ""
      s = self._cmdstr(cmd + [
        "-t",f"{name}_prod:{version}",
        "--progress=plain",
        "--target","production","."],_show=True)
      if "Check complete, no warnings found" not in s: r += s
      cmd.append("--build-arg"); cmd.append(f"GID={os.getresgid()[0]}")
      cmd.append("--build-arg"); cmd.append(f"UID={os.getuid()}")
      s += self._cmdstr(cmd + [
        "-t",f"{name}_dev:{version}",
        "--progress=plain",
        "--build-context","projects=../../projects",
        "--target","development","."
        ],_show=True)
      if "Check complete, no warnings found" not in s: r += s
      return r
    else:
      self._cmdInteractive(cmd + [
        "-t",f"{name}_prod:{version}",
        "--progress=plain",
        "--target","production","."],_show=True)
      cmd.append("--build-arg"); cmd.append(f"GID={os.getresgid()[0]}")
      cmd.append("--build-arg"); cmd.append(f"UID={os.getuid()}")
      self._cmdInteractive(cmd + [
        "-t",f"{name}_dev:{version}",
        "--progress=plain",
        "--build-context","projects=../../projects",
        "--target","development","."
        ],_show=True)
    # Removes all stopped containers, all networks not used by at least one
    # container, all dangling images (untagged image layers that are no
    # longer used by any images), and unused build cache. 
    self._cmdInteractive([
      "docker",
      "system",
      "prune",
      "-f"
      ],_show=True)
    # Remove unused build cache
    self._cmdInteractive([
      "docker",
      "builder",
      "prune",
      "-f"
      ],_show=True)
    self._touch(touchfile)

  def _dkrun_release_env(self,prod:bool=True) -> None:
    """ Replace variables in release.env. """
    with open(self.dkr,"r") as r, open(self.dkdr,"w") as w:
      for line in r:
        if line.startswith("PROD_"):
          if not prod: continue
          line=line[5:]
        if line.startswith("DEV_"):
          if prod: continue
          line=line[4:]
        if "USERID" in line:
          w.write(f"USERID={os.getuid()}{os.linesep}")
        elif "GROUPID" in line:
          w.write(f"GROUPID={os.getresgid()[0]}{os.linesep}")
        elif "_DATA" in line:
          # TODO; recreate directory.
          pass
        elif "_FILE" in line:
          # TODO; ??
          pass
        else:
          w.write(line)

  def dkrun(self, service:str) -> None:
    """ Run a service in example/docker-compose.yml
      :param service: the service to run.
    """
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
    self._dkrun_release_env(prod=False)
    try:
      self._cmd(["docker","stop",container_name],_show=True)
      self._cmd(["docker","rm",container_name],_show=True)
    except Exception:
      pass
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkr,
                           "run","orphans","--name",container_name,"-it",service,"/bin/bash"],_show=True)
    self._cmd(["docker","stop",container_name],_show=True)
    self._cmd(["docker","rm",container_name],_show=True)

  def dkpull(self) -> None:
    """ Download images in release.env, PULL_* """ 
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
          if self._cmd(["docker","images","-q",tag],_show=True):
            print(f"Image {tag} already present, wont attemp to repull the remote image")
          else:
            self._cmd(["docker","pull",image],_show=True)
            self._cmd(["tag",image,tag],_show=True)

  def dklogs(self,service:str=None) -> None:
    """ Tails the logs from services in example/docker-compose.yml
    :param service: select a service. Default is logs from all services.
    """
    if self._getpreference(self._name,False) == False: return;
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=False)
    p = ["--follow"]
    if service: p += [service]
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "logs"]+p,_show=True)

  def dkexec(self,cmd:str,service:str=None,user:str=None) -> None:
    """ Run a command inside a service started by compose.yaml
    :param cmd: Command to run inside the container
    :param service: Optional name of the service to identify the container. Default expects one service and selects that.
    :param user: Switch to this user to run the command, otherwise use the container default user.
    """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=False)
    if not service:
      services = self._cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "ps","--services"],_show=True)
      if not services:
        print("no running services")
        return
      if len(services) > 1:
        print(f"{services} running services, please select service using option --container")
        return
      service=services[0]
    c = ["docker","compose","-f",self.dkdc,"--env-file",self.dkdr]
    c += ["exec","-it"]
    if user: c += ["-u",user]
    c += [service,cmd]
    self._cmdInteractive(c,_show=True)

  def dkup(self) -> None:
    """ Run the services in example/docker-compose.yml """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=False)
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "up","--detach"],_show=True)

  def dkupprd(self) -> None:
    """ Run the services in example/docker-compose.yml """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=True)
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "up","--detach"],_show=True)

  def dkdown(self) -> None:
    """ Stop the services in docker-compose """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=False)
    self._cmdInteractive(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "down"],_show=True)
    self._cmdInteractive(["docker","network","prune","-f"],_show=True)

  def dkreup(self) -> None:
    """ Simulates a restart of the services without recreating DATA/FILE i.e. persistent state. """
    if not os.path.exists(self.dkdc):
      print(f"{self.dkdc} does not exist")
      return
    self._dkrun_release_env(prod=False)
    self._cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "down"],_show=True)
    self._cmd(["docker","compose","-f",self.dkdc,"--env-file",self.dkdr,
                "up","--detach"],_show=True)

  def dkimages(self,_show:bool=False) -> str:
    """ Detect prod or dev images. """
    name = self.name()
    version = self.version()
    prod = self._cmd(["docker","images","-q",f"{name}_dev:{version}"],_show=_show)
    dev = self._cmd(["docker","images","-q",f"{name}_prod:{version}"],_show=_show)
    return ("yes/prod" if prod else "no/prod") + " " + ("yes/dev" if dev else "no/dev")

  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._work_align()+["c"]

  def _workTitles(self) -> list:
    """ Titles for work """
    return super()._workTitles()+["dkimages\nlocal>local\ndkbuild"]

  def _work(self) -> list:
    """ Gather project work """
    self.dkcheck(_show=False)
    images = self.dkimages(_show=False)
    images = "" if images == "yes/prod yes/dev" else images
    return super()._work()+[images]

  def _upversion(self,version:str,oldversion:str) -> str:
    """ Update files with the build version. """
    name=self.name()
    if os.path.exists(self.dkr):
      self._sed(self.dkr,f'IMAGE\s*=\s*{name}:.*',f'IMAGE={name}:{version}')
      self._sed(self.dkr,f'RELEASE\s*=\s*{name}.*',f'RELEASE={name}:{version}')
    if os.path.exists(self.dkf):
      self._sed(self.dkf,f'{name}:[0-9.]*',f'{name}:{version}')
      self._sed(self.dkf,f'{name}==[0-9.]*',f'{name}=={version}')
    if os.path.exists(self.dkf):
      self._sed(self.dkf,f'{name}==[0-9.]*',f'{name}=={version}')