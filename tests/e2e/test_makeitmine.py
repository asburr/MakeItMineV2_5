from makeitminev2_5.makeutils import MakeUtils
import os
import pytest


@pytest.mark.e2e
class Test_makeitmine():

  exe = ["docker-compose","-f","compose.yaml","--env-file","dkrun_release.env",
         "exec", "-w","/MakeItMine","-it", "gitserver"]
  R=os.path.join("/","remotegit","testing")
  L=os.path.join("/","test_projects","testing")
  m=os.path.join("/","projects","MakeItMineV2_5","MakeItMine.sh")
  x=MakeUtils()
  testpy = "src/testing/testing.py"

  @classmethod
  def lcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdInteractive([cls.m]+cmd,fail=fail,_show=_show)

  @classmethod
  def rcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdstr(cls.exe+cmd,fail=fail,_show=_show,stderr=True)

  @classmethod
  def setup_class(cls):
    cls.teardown_class()
    cls.lcmd(["dkup"],fail=True,_show=True)

  @classmethod
  def teardown_class(cls):
    cls.lcmd(["dkdown"],fail=False,_show=True)

  @pytest.mark.skip
  def test_container(self):
    r = self.rcmd(["whoami"],fail=True,_show=True)
    assert r=="appuser"

  @pytest.mark.skip
  def test_status_norepo(self):
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtsetupshow" in r
    assert "gtsetup" in r
    assert "not a repo" in r

  def test_repo(self):
    """ workflow #1: create a remote repo. """
    os._exit(1)
    self.rcmd([self.m,"gtremoterepo",self.R],fail=True,_show=True)

  def test_gtsetup(self):
    """ workflow #2: create a local repo that is connected to the remote repo. """
    self.rcmd([self.m,"gtsetup","--location",self.R,"--name","appuser",
               "--email","appuser@appgroup.test"],fail=True,_show=True)

  @pytest.mark.skip
  def test_status_newrepo(self):
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtinitshow" not in r
    assert "gtsetup" not in r
    assert "no repo" not in r

  @pytest.mark.skip
  def test_gtuntracked(self):
    self.rcmd([self.m,"touch",self.testpy,"--contents",""],fail=True,_show=True)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtuntracked" in r
    assert "gtadd" in r
    assert "1/files" in r
    self.rcmd([self.m,"delete",self.testpy],fail=True,_show=True)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtuntracked" not in r
    assert "gtadd" not in r
    assert "1/files" not in r

  def test_pysync(self):
    self.rcmd([self.m,"delete","poetry.lock"],fail=False,_show=True)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "pycheck" in r
    assert "pysync" in r
    assert "Missing lock" in r
    self.rcmd([self.m,"pysync"],fail=True,_show=True)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "pycheck" not in r
    assert "pysync" not in r
    assert "Missing lock" not in r

  @pytest.mark.skip
  def test_checkfile(self):
    contents="import os\nimport datetime #Not used\nos.getcwd()\nx = y + 1 # y not defined\nos.junk() # no method"
    self.rcmd([self.m,"touch",self.testpy,"--contents",contents],fail=True,_show=True)
    r = self.rcmd([self.m,"checkfile","--file",self.testpy],fail=False,_show=True)
    assert "`datetime` imported but unused" in r
    assert "Undefined name `y`" in r
    assert "os.junk() # no method" in r
    self.rcmd([self.m,"delete",self.testpy],fail=True,_show=True)

  def test_pypackage(self):
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "pypackage" in r
    r = self.rcmd([self.m,"pypackage"],fail=True,_show=True)
    assert "pypackage" not in r

  def test_dkbuild(self):
    os._exit(1)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "dkbuild" in r
    r = self.rcmd([self.m,"dkbuild"],fail=True,_show=True)
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "dkbuild" not in r
    r = self.rcmd([self.m,"dkiamges"],fail=True,_show=True)
    assert "yes/prod yes/dev" in r
