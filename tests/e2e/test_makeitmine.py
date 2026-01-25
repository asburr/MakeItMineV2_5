from makeitminev2_5.makeutils import MakeUtils
import os
import pytest
from pathlib import Path


class MIMcontainer():
  """ The container used by all testcases. """

  exe = ["docker-compose","-f","compose.yaml","--env-file","dkrun_release.env",
         "exec", "-it", "gitserver"]
  R=os.path.join("/","remotegit","testing")
  L=os.path.join("/","test_projects","testing")
  C=os.path.join("/","cloned_projects","testing")
  lm=os.path.join(Path.home(),"projects","MakeItMineV2_5","MakeItMine.sh")
  m=os.path.join("/","projects","MakeItMineV2_5","MakeItMine.sh")
  x=MakeUtils()
  testpy = "src/testing/testing.py"

  @classmethod
  def lcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdInteractive([cls.lm]+cmd,fail=fail,_show=_show)

  @classmethod
  def rcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdstr(cls.exe+cmd,fail=fail,_show=_show,stderr=True)

  @classmethod
  def rcmdInteractive(cls,cmd:list,fail:bool,_show:bool) -> None:
    cls.x._cmdInteractive(cls.exe+cmd,fail=fail,_show=_show)


@pytest.fixture(scope="session") # Run container once for the session.
def container():
  """ Uses MIM to create a container where other MIM functionality is tested. """
  container = MIMcontainer()
  container.lcmd(["dkdown"],fail=False,_show=True)
  container.lcmd(["dkup"],fail=True,_show=True)
  r = container.rcmd(["whoami"],fail=True,_show=True)
  assert r=="appuser"
  yield container # Test cases run here.
  container.lcmd(["dkdown"],fail=True,_show=True)


@pytest.mark.e2e
@pytest.mark.usefixtures("container")
class Test_repo():
  """ Git setup. """

  def test_status_norepo(self,container):
    """ gtsetup as work """
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "gtsetupshow" in r
    assert "gtsetup" in r
    assert "not a repo" in r

  @pytest.mark.dependency()
  def test_gtremoterepo(self,container):
    """ Create a remote repo. """
    container.rcmdInteractive([container.m,"gtremoterepo",container.R],fail=True,_show=True)

  @pytest.mark.dependency()
  @pytest.mark.dependency(depends=["Test_repo::test_gtremoterepo"])
  def test_gtsetup(self,container):
    """ Create a local repo connected to the remote repo and setup the git user. """
    container.rcmdInteractive([
      container.m,"gtsetup","--location",container.R,"--name","appuser",
      "--email","appuser@appgroup.test"],fail=True,_show=True)
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "gtinitshow" not in r
    assert "gtsetup" not in r
    assert "no repo" not in r


@pytest.mark.e2e
@pytest.mark.usefixtures("container")
@pytest.mark.dependency(depends=["Test_repo::test_gtsetup"])
class Test_gt():
  """ Git commands. """

  def test_gtuntracked(self,container):
    """ Add a new file and make sure it is reported as untracked. """
    container.rcmdInteractive([
      container.m,"touch",container.testpy,"--contents",""],
      fail=True,_show=True)
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "gtuntracked" in r
    assert "gtadd" in r
    assert "1/files" in r
    container.rcmdInteractive([
      container.m,"delete",container.testpy],fail=True,_show=True)
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "gtuntracked" not in r
    assert "gtadd" not in r
    assert "1/files" not in r

# TODO;
#  def test_gtclone(self,,container):
#    """ Clone repo. """
#  def test_gtlocalbranch(self,container):
#    """ Add branch to clone. """
#  def test_gtbranch(self,container):
#    """ Dev branch in cloned repo. """
#  def test_gttrackingremotebranch(self,container):
#    """ ?? """
#  def test_gtpush(self,container):
#    """ save changes to remote branch. """
#  def test_gtrelease(self,container):
#    """ Release remote branch into main. """
#  def test_gtrebasemain(self,container):
#    """ Pull changes from main into local branch. """
#  def test_gtrebaseremote(self,container):
#    """ Pull changes in remote branch into local branch. """
#  def test_gtadd(self,container):
#    """ Add local files to the commit....is this needed as commit does this automatically? """
#  def test_gtfetch(self,container):
#    """ fetch is called when needed, is this needed as a separate functionality? """
#  def test_gttag(self,container):
#    """ Tag the main branch """


@pytest.mark.e2e
@pytest.mark.usefixtures("container")
@pytest.mark.dependency(depends=["Test_repo::test_gtsetup"])
class Test_py():
  """ Python commands """

  def test_pysync(self,container):
    """ Sync the pyproject.toml with the venv. """
    # TODO; Check that there is no pyproject.toml, venv, and lock file.
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "pycheck" in r
    assert "pysync" in r
    assert "Missing lock" in r
    container.rcmdInteractive([container.m,"pysync"],fail=True,_show=True)
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "pycheck" not in r
    assert "pysync" not in r
    assert "Missing lock" not in r
    container.rcmd(["ls","pyproject.toml","poetry.lock"],fail=True,_show=True)

  # @pytest.mark.skip
  def test_checkfile(self,container):
    """ Check a python file. """
    contents="import os\nimport datetime #Not used\nos.getcwd()\nx = y + 1 # y not defined\nos.junk() # no method"
    container.rcmd([container.m,"touch",container.testpy,"--contents",contents],fail=True,_show=True)
    r = container.rcmd([container.m,"checkfile","--file",container.testpy],fail=False,_show=True)
    assert "`datetime` imported but unused" in r
    assert "Undefined name `y`" in r
    assert "os.junk() # no method" in r
    container.rcmd([container.m,"delete",container.testpy],fail=True,_show=True)

  def test_pypackage(self,container):
    """ Build a package for the Python software, use MIM to install the wheel.
    """
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "pypackage" in r
    r = container.rcmd([container.m,"pypackage"],fail=True,_show=True)
    assert "pypackage" not in r
    container.rcmd(["ls",".download"],fail=True,_show=True)
    wheel = container.rcmd([container.m,"pywheel"],fail=True,_show=True)
    container.rcmd(["poetry","run","pip","install",wheel],fail=True,_show=True)
    container.rcmd([container.m,"delete",container.testpy],fail=True,_show=True)


@pytest.mark.e2e
@pytest.mark.usefixtures("container")
@pytest.mark.dependency(depends=["Test_repo::test_gtsetup"])
class Test_dk():
  """ Test docker (dk). """

  def test_dkbuild(self,container):
    """ Build the docker container. """
    r = container.rcmd([container.m,"dkimages"],fail=True,_show=True)
    if "yes" in r:
      version = container.rcmd([container.m,"version"],fail=True,_show=True)
      assert version
      container.rcmd(["docker","rmi",f"testing_dev:{version}"],fail=False,_show=True)
      container.rcmd(["docker","rmi",f"testing_prod:{version}"],fail=False,_show=True)    
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "dkbuild" in r
    r = container.rcmd([container.m,"dkbuild"],fail=True,_show=True)
    r = container.rcmd([container.m,"work"],fail=True,_show=True)
    assert "dkbuild" not in r
    r = container.rcmd([container.m,"dkimages"],fail=True,_show=True)
    assert "yes/prod yes/dev" in r
# TODO;
#  def dkcheck(self,container):
#  def dkbuild(self,container):
#      :param buildargk: Keys for build-arg.
#      :param buildargv: Values for build-arg.
#      :param secret: semicolon separated of id=<id>,src=<path>.
#      :param check: checks the Dockerfile and does not build anything.
#  def dkrun(self,container):
#      :param service: the service to run.
#  def dkpull(self,container):
#  def dklogs(self,container):
#    :param service: select a service. Default is logs from all services.
#  def dkexec(self,container):
#    :param cmd: Command to run inside the container
#    :param service: Optional name of the service to identify the container. Default expects one service and selects that.
#    :param user: Switch to this user to run the command, otherwise use the container default user.
#  def dkup(self,container):
#  def dkupprd(self,container):
#  def dkdown(self,container):
#  def dkreup(self,container):

@pytest.mark.e2e
@pytest.mark.usefixtures("container")
@pytest.mark.dependency(depends=["Test_repo::test_gtsetup"])
class Test_ws():
  """ Test workspace (ws). """
  pass
# TODO;
# def test_wsset(self,container):
# def test_ws(self) -> None:
# def test_wsadd(self,container):
#    :param pj: project name, defaults to current directory.
#    :param path: path to the root of the project, defaults to current directory.
# def test_wsrm(self,container):
#    :param pj: project name, defaults to current directory.
# def test_wswork(self,container):
#    :param pj: project name, defaults to current directory.
# def test_wsrun(self,container):
#    :param pj: project name, defaults to current directory.
#    :param args: arguments for cmd.
#    :param kwargs: keyword arguments for cmd.
