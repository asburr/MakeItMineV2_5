from makeitminev2_5.makeutils import MakeUtils
import os
import pytest


@pytest.mark.e2e
class Test_makeitmine():

  compose = os.path.join("example","docker-compose.yaml")
  env = os.path.join("example","release.env")
  cmd = ["docker-compose","-f",compose,"--env-file",env]
  exe = cmd + ["exec", "--user", "root", "gitserver"]
  R=os.path.join("/","remotegit","MakeItMine")
  L=os.path.join("/","MakeItMine")
  m=os.path.join("/","MakeItMine","MakeItMine.sh")
  x=MakeUtils()

  @classmethod
  def setup_class(cls):
    cls.teardown_class()
    if not cls.x._cmd(cls.cmd,fail=False,_show=True):
      print(f"ERROR: install {cls.cmd}\nhint: https://github.com/docker/compose/releases")
      os._exit(1)
    if not os.path.exists(cls.compose):
      print(f"{cls.compose} does not exist")
      os._exit(1)
    cls.x._cmdInteractive(cls.cmd+["up","--detach"],_show=True)

  @classmethod
  def teardown_class(cls):
    cls.x._cmdInteractive(cls.cmd+["down"],fail=False,_show=True)

  def test_container(self):
    r=self.x._cmdstr(self.exe+["whoami"],_show=True)
    assert r=="root"

  def test_makeitmine(self):
    r=self.x._cmdstr(self.exe+[self.m,"status"],_show=True)
    assert r=="root"

  def test_repo(self):
    self.x._cmdInteractive(self.exe+[self.m,"gtremoterepo",self.R],_show=True)
    os.chdir(self.L)
    self.x._cmdInteractive(cmd=[self.m,"gtcreate",self.R],_show=True)