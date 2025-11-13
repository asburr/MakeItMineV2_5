import argparse
import os
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

  def _gtremotechanges(self,localbranch) -> str:
    """ Changes published to the remote branch that need merging into main. """
    return self._cmd(["git","diff","--name-only",f"origin/{localbranch}..origin/main"]).strip()

  def gtlocalcommits(self) -> str:
    """ Changes commited to the local branch but not published remotely. """
    return self._cmd(["git","diff","--name-only","origin","HEAD"]).strip()
    
  def gtlocalchanges(self) -> str:
    """ Changes made locally but not commited. """
    return self._cmd(["git","diff","--name-only"]).strip()

  def _gtcommit_branch(self,localbranch:str) -> str:
    """ merge-base finds the ancestor [commit id] for the local branch """
    return self._cmd(["git","merge-base","main",localbranch]).strip()
    
  def gtcommit_main(self) -> str:
    """ rev-parse finds the ancestor [commit id] for the main branch """
    return self._cmd(["git","rev-parse","origin/main"]).strip()

  def gtremotebranch(self) -> bool:
    """ Does localbranch exist remotely? """
    localbranch = self.gtlocalbranch()
    self._cmd(["git","fetch"],show=True)
    for branch in self._cmd(["git","branch","-r"],show=True).split(os.linesep):
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
    """ Commit and push changes remotely """
    if self.gtlocalchanges():
      self._cmdInteractive(["git","commit","."],show=True)
    if self.gtremotebranch():
      self._cmd(["git","push"],show=True)
      return
    # -u setups tracking between the new remote branch and the existing local branch
    localbranch = self.gtlocalbranch()
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
        print("Nothing to rebase, {localbranch} is up to date with main")
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

  def gtremote(self,url:str) -> None:
    """ Setup the remote URL for a newly created local project. """
    for u in self._cmd(["git","remote","get-url","origin","--all"],show=True).split(os.linesep):
      if u != url:
        print(f"different url in .git/config please edit to delete the url {u}")
        os._exit(1)
      else:
        print(f"{url} already in .git/config wont readd")
        return
    self._cmd(["git","remote","set-url","--add","origin",url],show=True)

  def _showTitles(self) -> list:
    """ Titles for show """
    return super()._showTitles()+["branch","remote"]

  def _show(self) -> list:
    """ Gather project status """
    return super()._show()+[f"{self.gtlocalbranch()}","sid dd:mm"]

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters. """
    super()._main(ap)
    ap.add_argument('-b', '--branch', help="Branch for gtbranch")
    cls.command_parameters["gtbranch"] = ["branch"]
    ap.add_argument('-u', '--url', help="URL of remote git project for gtremote")
    cls.command_parameters["gtremote"] = ["url"]


if __name__ == "__main__":
  GtMake.main()

      