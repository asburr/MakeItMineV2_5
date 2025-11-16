import argparse
import os
import datetime
from MakeItMineV2_5.make import Make


class GtMake(Make):
  """ Platform independent recipies for a Makefile supporting a GIT project.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.gitignore=".gitignore"

  def files(self) -> list:
    return super().files() + [self.gitignore]

  def gtignore(self) -> None:
    """ Create or append to .gitignore in current working directory. """
    l = [".git",".spyproject", "__pycache__/", "*.py[cod]","dist/","venv/"]    
    if not os.path.exists(self.gitignore):
      print("creating {self.gitignore}")
      with open(self.gitignore,"w") as f:
        for s in l:
          f.write(f"{s}{os.linesep}")
      return
    with open(self.gitignore,"r") as f:
      for line in f:
        try:
          l.remove(line.strip())
        except:
          pass
    with open(self.gitignore,"a") as f:
      for s in l:
        print(f"Adding {s} to .gitignore")
        f.write(f"{s}{os.linesep}")

  def gtlocalbranch(self) -> None:
    """ Name of the local branch """
    return self._cmd(["git","branch","--show-current"]).strip()

  def gtcommit_branch(self) -> str:
    """ merge-base finds the ancestor [commit id] for the local branch """
    localbranch = self.gtlocalbranch()
    return self._cmd(["git","merge-base","main",localbranch],show=True).strip()
    
  def gtcommit_origin(self) -> str:
    """ rev-parse finds the ancestor [commit id] for the origin of the branch """
    localbranch = self.gtlocalbranch()
    return self._cmd(["git","rev-parse",f"origin/{localbranch}"],show=True).strip()

  def gttrackingremotebranch(self) -> bool:
    """ Does localbranch track a remote branch? """
    localbranch = self.gtlocalbranch()
    self._cmd(["git","fetch"],show=True)
    for branch in self._cmd(["git","config","--get",f"branch.{localbranch}.remote"],show=True,fail=False).split(os.linesep):
      if localbranch in branch: return True
    return False

  def gtbranch(self,branch:str) -> None:
    """ Switch to a branch. Create branch locally if it does not exist. """
    localbranch = self.gtlocalbranch()
    if localbranch == branch:
      print(f"already on {branch}")
      return
    self._cmd(["git","fetch"],show=True)
    if branch in self._cmd(["git","branch","--list"],show=True).split("\n"):
      self._cmd(["git","switch",branch],show=True)
      self._cmd(["git","pull",branch],show=True)
      return
    if branch == "main":
      print("Cannot create main branch")
      return
    self._cmd(["git","branch",branch],show=True)
    self._cmd(["git","switch",branch],show=True)

  def gtpush(self) -> None:
    """ Commit and push to remote branch """
    if self.gtlocalchanges():
      self._cmdInteractive(["git","commit","."],show=True)
    localbranch = self.gtlocalbranch()
    if not self.gttrackingremotebranch():
      self._cmd(["git","branch",f"--track=origin/{localbranch}"],show=True)
    if self.gtcommit_origin() != self.gtcommit_branch():
      print("Remote branch is ahead of local branch")
      self._cmd(["git","pull"],show=True)
    # -u setups tracking between the new remote branch and the existing local branch
    self._cmd(["git","push","-u","origin",localbranch],show=True)

  def gtmerge(self) -> None:
    """ TO TEST: merge current branch into main branch """
    if self.gtlocalchanges():
      print("Error, commit local changes before merge")
      return
    localbranch = self.gtlocalbranch()
    if localbranch == "main":
      print("Error, on main branch and must be on a developer branch")
      return
    self._cmd(["git","checkout","main"],show=True)
    self._cmd(["git","fetch"],show=True)
    self._cmd(["git","pull"],show=True)
    self._cmd(["git","merge","--no-ff",localbranch],show=True)
    self._cmd(["git","push"],show=True)

  def gtancestor(self) -> str:
    """ common ancester between main and localbranch. """
    localbranch = self.gtlocalbranch()
    self._cmd(["git","fetch","origin"],show=True)
    return self._cmd(["git","merge-base","main",localbranch],show=True,fail=True)
    
  def gtmainhead(self) -> str:
    """ head of origin main branch """
    return self._cmd(["git","show-ref","--heads","-s","origin","main"],show=True,fail=True)

  def gtrebase(self) ->  None:
    """ TO TEST: rebase working branch with any new changes in main. """
    status = self._cmd(["git","status"],show=True)
    if "interactive rebase in progress" in status:
      print("INPROGRESS; rebase already in progress")
      self._cmdInteractive(["git","rebase","--continue"],show=True)
      return
    if self.gtlocalchanges():
      print("Error, commit local changes before merge")
      return
    localbranch = self.gtlocalbranch()
    if localbranch == "main":
      if "Your branch is behind" not in status:
        print(f"Nothing to rebase, {localbranch} is up to date with main")
        return
      self._cmd(["git","fetch"],show=True)
      self._cmdInteractive(["git","rebase"],show=True)
    else:
      ancestor = self.gtancestor()
      mainancestor = self.gtmainhead()
      if ancestor == mainancestor:
        print(f"Nothing to rebase, {localbranch} is up to date with main")
        return
      self._cmd(["git","fetch","origin"],show=True)
      self._cmdInteractive(["git","rebase","origin/main"],show=True)

  def gtlistfiles(self) -> str:
    """ List local files that are not tracked by git. """
    return self._cmd(["git","ls-files","--others","--exclude-standard"],show=True)

  def gtadd(self) -> str:
    """ Add local untracked files to git. """
    files = [file for file in self.gtlistfiles().split(os.linesep) if file]
    if files: self._cmd(["git","add"]+files,show=True)

  def gtcreate(self) -> None:
    """ Create a Git repository from the current working directory.
        Asks the user for the URL for the remote repo.
    """
    status = self._cmd(["git","status"],show=True,fail=False)
    if "fatal: not a git repository" not in status:
      print("Already a git project")
    url=input("Create the remote repo and enter the URL:")
    self.gtignore()
    self._cmdInteractive(["git","init","--initial-branch","main","."],show=True)
    self._cmd(["git","add"]+self.files(),show=True)
    self.gtadd()
    self._cmd(["git","remote","set-url","--add","origin",url],show=True)
    self.gtpush()

  def gtsetremote(self,url:str) -> None:
    """ Setup the remote URL for a newly created local project. """
    for u in self._cmd(["git","remote","get-url","origin","--all"],show=True).split(os.linesep):
      if u != url:
        print(f"different url in .git/config please edit to delete the url {u}")
        os._exit(1)
      else:
        print(f"{url} already in .git/config wont readd")
        return
    self._cmd(["git","remote","set-url","--add","origin",url],show=True)

  def _show_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._show_align()+["l","l","l"]

  def gtgetremote(self) -> str:
    """ Get origin for the remote branch. """
    return self._cmd(["git","rev-parse","--abbrev-ref","--symbolic-full-name","@{u}"],show=False).split("/")[2]

  def gtorigin(self,show=True) -> str:
    """ Epoch and sid for the last change on origin in dd:hh:mm. """
    branch = self.gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}"],show=show).split("\n")[0].split(" ")
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"origin/{branch} {a[1]} {dd:>02d}:{hh:>02d}:{mm:>02d}"

  def gtoriginfiles(self,show=True) -> str:
    """ Changes made in origin of this branch that need rebasing into branch. """
    branch = self.gtlocalbranch()
    return self._cmd(["git","diff","--name-only",f"origin/{branch}..HEAD"],show=show).strip()

  def gtremote(self,show=True) -> str:
    """ Epoch and sid for the lastest change on remote branch in dd:hh:mm. """
    branch = self.gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}"],show=show).split("\n")[0].split(" ")
    if not a[0]: return branch
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{branch} {a[1]} {dd:>02d}:{hh:>02d}:{mm:>02d}"

  def gtremotefiles(self) -> str:
    """ Changes published to the remote branch that need merging into local branch (HEAD). """
    branch=self.gtlocalbranch()
    return self._cmd(["git","diff","--name-only",f"origin/{branch}..HEAD"]).strip()

  def gtlocal(self,show=True) -> str:
    """ Epoch and sid for the lastest change on local branch in dd:hh:mm. """
    branch = self.gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"{branch}..origin/{branch}"],show=show).split("\n")[0].split(" ")
    if not a[0]: return branch
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{branch} {a[1]} {dd:>02d}:{hh:>02d}:{mm:>02d}"

  def gtlocalfiles(self,show=True) -> str:
    """ Changes commited to the local branch but not published remotely. """
    branch = self.gtlocalbranch()
    return self._cmd(["git","diff","--name-only",f"{branch}..origin/{branch}"],show=show).strip()
    
  def _showTitles(self) -> list:
    """ Titles for show """
    return super()._showTitles()+["gtlocal","gtremote","gtorigin"]

  def _show(self) -> list:
    """ Gather project status """
    return super()._show()+[self.gtlocal(show=False),self.gtremote(show=False),self.gtorigin(show=False)]

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters. """
    super()._main(ap)
    ap.add_argument('-b', '--branch', help="Branch for gtbranch")
    cls.command_parameters["gtbranch"] = ["branch"]
    ap.add_argument('-u', '--url', help="URL of remote git project for gtsetremote")
    cls.command_parameters["gtsetremote"] = ["url"]


if __name__ == "__main__":
  GtMake.main()

      