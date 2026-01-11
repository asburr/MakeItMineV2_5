from makeitminev2_5.makeutils import MakeUtils
import os
import pytest


@pytest.mark.e2e
class Test_makeitmine():

  exe = ["docker-compose","-f","compose.yaml","--env-file","dkrun_release.env",
         "exec", "-w","/MakeItMine","-it", "gitserver"]
  R=os.path.join("/","remotegit","MakeItMine")
  L=os.path.join("/","MakeItMine")
  m=os.path.join("/","projects","MakeItMineV2_5","MakeItMine.sh")
  x=MakeUtils()
  mim = ["./MakeItMine.sh"]

  @classmethod
  def lcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdInteractive(cls.mim+cmd,fail=fail,_show=_show)

  @classmethod
  def rcmd(cls,cmd:list,fail:bool,_show:bool) -> any:
    return cls.x._cmdstr(cls.exe+cmd,fail=fail,_show=_show)

  @classmethod
  def setup_class(cls):
    cls.teardown_class()
    cls.lcmd(["dkup"],fail=True,_show=True)

  @classmethod
  def teardown_class(cls):
    cls.lcmd(["dkdown"],fail=False,_show=True)

  def test_container(self):
    r = self.rcmd(["whoami"],fail=True,_show=True)
    assert r=="appuser"

  def test_status_norepo(self):
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtinitshow" in r
    assert "gtsetup" in r
    assert "no repo" in r

  def test_repo(self):
    """ workflow #1: create a remote repo. """
    self.rcmd([self.m,"gtremoterepo",self.R],fail=True,_show=True)

  def test_create(self):
    """ workflow #2: create a local repo that is connected to the remote repo. """
    self.rcmd([self.m,"gtsetup","--location",self.R,"--name","appuser","--email","appuser@appgroup.test"],fail=True,_show=True)

  def test_status_newrepo(self):
    r = self.rcmd([self.m,"work"],fail=True,_show=True)
    assert "gtinitshow" not in r
    assert "gtsetup" not in r
    assert "no repo" not in r
