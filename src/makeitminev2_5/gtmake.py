import argparse
import os
import datetime
from makeitminev2_5.make import Make


class GtMake(Make):
  """ Platform independent recipies for a Makefile supporting GIT. Trunk
  based developement is working on temporary branches directly off main.
  """

  def _build(self,pj:str) -> None:
    """ build the project. """
    super._build(pj)

  def _test(self,pj:str) -> None:
    """ test """
    super._test(pj)

  def _upversion(self,pj:str,version:str,oldversion:str) -> str:
    """ Update files containing version from BUILDVERSION.txt. """
    if os.path.exists(self.ci):
      self._sed(self.ci,'docker_image_version\s*:.*',f'docker_image__version: {version}')
    super._upversion(pj,version,oldversion)

  def _upversionneeded(self,version:str,oldversion:str) -> bool:
    """ Only up version when there are changes in the project """
    a = self._cmd(['git','diff','name-only','origin/main'],show=True).split(os.linesep)
    return self.bv in a

  def _changes(self,pj:str) -> bool:
    """ Any changes to the project. """
    return super._changes(pj)

  def _statuswarning(self) -> list:
    if self._gtlocalbranch() == "main":
      return ["warning (git): You are working on the main branch.\nHint: create a developer branch using 'gtbranch <branch name>'"]
    
  def _status_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._status_align()+["l","l","l","l","l","l","l"]

  def _statusTitles(self) -> list:
    """ Titles for status """
    return super()._statusTitles()+[
      "gtuntracked\n>local\ngtadd",
      "gtunstaged\n>local\ngtadd",
      "gtmainahead\nmain>local\ngtrebasemain",
      "gtremoteahead\nremote>local\ngtrebaseremote",
      "gtuncommitted\nchange>local\ngtpush",
      "gtremotebehind\nlocal>remote\ngtpush",
      "gtmainbehind\nremote>main\ngtrelease"]

  def _status(self) -> list:
    """ Gather project status """
    self.gtfetch(show=False)
    untracked = self.gtuntracked(show=False)
    unstaged = self.gtunstaged(show=False)
    remote = self.gtremoteahead(show=False)
    main = self.gtmainahead(show=False)
    localremote = self.gtmainbehind(show=False)
    return super()._status()+[untracked,unstaged,main,remote,self.gtuncommitted(),self.gtremotebehind(show=False),localremote]

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.gitignore=".gitignore"
    self.ci = ".gitlab-ci.yml"

  def _files(self) -> list:
    """ Perminant files that can be created by this class. """
    return super()._files() + [self.gitignore,self.ci]

  def _gtignore(self) -> None:
    """ Create or append to .gitignore in current working directory. """
    l = [".*/", "__pycache__/", "*.py[cod]","dist/","venv/"]    
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
        
  def gtignore(self,pj:str=None) -> None:
    """ Create or append to .gitignore in current working directory. """
    self._setcwd(pj)
    self._gtignore()

  def gtignorefile(self,file:str,pj:str=None) -> None:
    """ Add file to git ignore. """
    if not os.path.exist(file):
      print(f"ERROR: No such file {file}")
      os._exit(1)
    self._setcwd(pj)
    filename = os.path.basename(file)
    if self._grep(self.gitignore,filename):
      print(f"INFO: {filename} in {self.gitignore}")
      return
    self._append(self.gitignore,filename)

  def _gtlocalbranch(self) -> str:
    """ Name of the local branch """
    return self._cmd(["git","branch","--show-current"])[0]

  def gtlocalbranch(self,pj:str=None) -> str:
    """ Name of the local branch """
    self._setcwd(pj)
    return self._gtlocalbranch()

  def gtclone(self,url:str,pj:str=None) -> None:
    """ clone workspace """
    if os.path.exists(pj):
      print(f"ERROR: {pj} already exists")
      os._exit(1)
    p = os.path.dirname(pj)
    if not os.path.exists(p):
      print(f"ERROR: porject root {p} must exists")
      os._exit(1)
    self._cmd(["git","clone",url,pj],show=True)

  def gtbranch(self,branch:str,pj:str=None) -> None:
    """ Switch to a branch. Create branch locally if it does not exist. """
    self._setcwd(pj)
    localbranch = self._gtlocalbranch()
    if localbranch == branch:
      print(f"already on {branch}")
      return
    self._cmd(["git","fetch"],show=True)
    if branch in self._cmd(["git","branch","--list"],show=True):
      self._cmd(["git","switch",branch],show=True)
      self._cmd(["git","pull",branch],show=True)
      return
    if branch == "main":
      print("Cannot create main branch")
      return
    self._cmd(["git","branch",branch],show=True)
    self._cmd(["git","switch",branch],show=True)

  def _gttrackingremotebranch(self) -> bool:
    """ Does localbranch track a remote branch? """
    localbranch = self._gtlocalbranch()
    self._cmd(["git","fetch"],show=True)
    for branch in self._cmd(["git","config","--get",f"branch.{localbranch}.remote"],show=True,fail=False):
      if "origin" == branch: return True
    return False

  def gttrackingremotebranch(self,pj:str=None) -> bool:
    """ Does localbranch track a remote branch? """
    self._setcwd(pj)
    return self._gttrackingremotebranch()

  def _gtpush(self) -> None:
    """ Commit and push to remote branch """
    if self.gtuncommittedfiles():
      self._cmdInteractive(["git","commit","."],show=True)
    localbranch = self._gtlocalbranch()
    if not self._gttrackingremotebranch():
      self._cmd(["git","branch",f"--track=origin/{localbranch}"],show=True)
    if self.gtremoteaheadfiles():
      print("Error: remote is ahead of local.\nHint: gtrebaseremote")
      return
    # -u setups tracking between the new remote branch and the existing local branch
    self._cmd(["git","push","-u","origin",localbranch],show=True)

  def gtpush(self,pj:str=None) -> None:
    """ Commit and push to remote branch """
    self._setcwd(pj)
    self._gtpush()

  def _gtrelease(self) -> None:
    """ TO TEST: release changes on remote branch into origin/main. """
    if self.gtlocalchanges():
      print("Error, commit local changes before merge")
      return
    branch = self._gtlocalbranch()
    if branch == "main":
      print("Error, on main branch and must be on a developer branch")
      return
    self._cmd(["git","checkout","main"],show=True)
    self._cmd(["git","fetch"],show=True)
    self._cmd(["git","pull"],show=True)
    self._cmd(["git","merge","--no-ff",branch],show=True)
    self._cmd(["git","push"],show=True)

  def _release(self) -> None:
    """ release """
    super._release()
    branch = self._gtlocalbranch()
    if branch == "main":
      self._gtrelease()
    else:
      self._gtpush()

  def gtrebasemain(self,pj:str=None) ->  None:
    """ TO TEST: rebase local branch with new changes on main. """
    self._setcwd(pj)
    status = self._cmd(["git","status"],show=True)
    branch = self._gtlocalbranch()
    if [x for x in status if "interactive rebase in progress" in x]:
      print("INPROGRESS; rebase already in progress")
      self._cmdInteractive(["git","rebase","--continue"],show=True)
      return
    if self.gtuncommittedfiles(show=False):
      print("Error, commit local changes (gtuncommittedfiles) before merge")
      return
    if self.gtremoteahead(show=False):
      print("ERROR gtrebasemain needed due to new changes on remote branch")
      return
    if branch == "main":
      print("ERROR use gtrebasemain when on main")
      return
    if not self.gtmainfiles():
      print(f"Nothing to rebase, {branch} is up to date with main")
      return
    self._cmd(["git","fetch","origin"],show=True)
    self._cmdInteractive(["git","merge","main"],show=True)

  def gtrebaseremote(self,pj:str=None) ->  None:
    """ TO TEST: rebase local branch with new changes on remote branch. """
    self._setcwd(pj)
    status = self._cmd(["git","status"],show=True)
    if [x for x in status if "interactive rebase in progress" in x]:
      print("ERROR gtrebasemain in progress")
      return
    if self.gtuncommittedfiles(show=False):
      print("ERROR gtpush local changes before merge")
      return
    self._cmdInteractive(["git","pull","origin","main"],show=True)

  def gtadd(self,pj:str=None) -> str:
    """ Add gtuntrackedfiles to git. """
    self._setcwd(pj)
    files = self.gtuntrackedfiles()
    if files: self._cmd(["git","add"]+files.split(os.linesep),show=True)
    files = self.gtunstagedfiles()
    if files: self._cmd(["git","add"]+files.split(os.linesep),show=True)

  def gtcreate(self,url,pj:str=None) -> None:
    """ Create a Git repository from the current working directory.
        Asks the user for the URL for the remote repo.
    """
    self._setcwd(pj)
    status = self._cmd(["git","status"],show=True,fail=False)
    if not self._substrin("fatal: not a git repository",status):
      print("Already a git project")
      return
    self._gtignore()
    self._cmdInteractive(["git","init","--initial-branch","main","."],show=True)
    self._cmd(["git","add"]+self._files(),show=True)
    self.gtadd()
    self._cmd(["git","remote","set-url","--add","origin",url],show=True)
    self._gtpush()

  def gtsetremote(self,url:str,pj:str=None) -> None:
    """ Setup the remote URL for a newly created local project. """
    self._setcwd(pj)
    for u in self._cmd(["git","remote","get-url","origin","--all"],show=True):
      if u != url:
        print(f"different url in .git/config please edit to delete the url {u}")
        os._exit(1)
      else:
        print(f"{url} already in .git/config wont readd")
        return
    self._cmd(["git","remote","set-url","--add","origin",url],show=True)

  #   three dot notation i.e. origin/branch...origin/main
  #   -=================-
  #   The three dots limits the difference to the work done on the branch on
  #   the right of the dots since the common ancestor with the branch on the
  #   left. In this case, the remote branch is on the right so it's showing
  #   changes in this branch, and the local branch is on the left so it
  #   linmited changes to the point at which the local branched from the
  #   remote.
  #   Therefore, it's showing changes in remote since local branched.
  #   Note the two dot notation. When used for diff, the two dots
  #   does not limited the difference but shows differences between the
  #   heads of both branches. Which is not what we want here, and three dots
  #   is what we need for diff.
  #   Also note that the dot notation has opposite behaviour with git log.
  #   two dot notation  i.e. origin/branch..origin/main.
  #   -===============-
  #   Note the two dots. When used for log, the two dots limits the list of
  #   commits to the work done on the right hand branch from the common
  #   ancestor with the branch on the left.
  #   Note the three dots. When used for log, the three dots does not
  #   limit the commit to any branch but shows all of the comments on both
  #   branches since the common ancestor. Which is not want we want here,
  #   and two dots is what we need for log.
  #   Also note that the dot notation has opposite behaviour with git diff.
  
  def gtmainahead(self,show=True) -> str:
    """ remote..main """
    branch = self._gtlocalbranch()
    if branch == "main": return "n/a on main"
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}..origin/main"],show=show).split("\n")[0].split(" ")
    if not a[0]: return f"0/files\n{branch}/br"
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    cnt = len(self.gtmainaheadfiles(show=False).split(os.linesep))
    return f"{cnt}/files\n{branch}/br\n{a[1]}/uid {dd:>02d}:{hh:>02d}:{mm:>02d}/age"

  def gtmainaheadfiles(self,show=True) -> str:
    """ remote..main """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/{branch}...origin/main"],show=show)

  def gtmainaheaddiff(self,show=True) -> str:
    """ remote..main """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/{branch}...origin/main"],show=show)

  def gtmainbehind(self,show=True) -> str:
    """ main..remote """
    branch = self._gtlocalbranch()
    if branch == "main": return "n/a on main"
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/main..origin/{branch}"],show=show).split("\n")[-1].split(" ")
    if not a: return f"0/files\n{branch}/br"
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    remote = a[1].split("/")[-1]
    cnt = len(self.gtmainbehindfiles(show=False).split(os.linesep))
    return f'{cnt}/files\n{branch}/br\n{remote}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age'

  def gtmainbehindfiles(self,show=True) -> str:
    """ Branch commits not released to main branch. """
    branch=self._gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/main...origin/{branch}"],show=show)

  def gtmainbehinddiff(self,show=True) -> str:
    """ Branch commits not released to main branch. """
    branch=self._gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/main...origin/{branch}"],show=show)

  def gtremoteahead(self,show=True) -> str:
    """ local..remote. """
    branch = self._gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"{branch}..origin/{branch}"],show=show)
    if not a: return f"0/files\n{branch}/br"
    a=a[-1].split(" ")
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]))
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    remote = a[1].split("/")[-1]
    cnt = len(self.gtremoteaheeadfiles(show=False).split(os.linesep))
    return f'{cnt}/files\n{branch}/br\n{remote}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age'

  def gtremoteaheadfiles(self,show=True) -> str:
    """ local...remote. """
    branch=self._gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"{branch}...origin/{branch}"],show=show)

  def gtremoteaheaddiff(self,show=True) -> str:
    """ local...remote. """
    branch=self._gtlocalbranch()
    return self._cmdstr(["git","diff",f"{branch}...origin/{branch}"],show=show)

  def gtuntracked(self,show:bool=True) -> str:
    """ Untracked local files. """
    cnt = len(self._cmd(["git","ls-files","--others","--exclude-standard"],show=show))
    return f'{cnt}/files'

  def gtuntrackedfiles(self,show:bool=True) -> str:
    """ Untracked local files. """
    return self._cmdstr(["git","ls-files","--others","--exclude-standard"],show=show)

  def gtunstaged(self,show:bool=True) -> str:
    """ Unstaged changes. """
    cnt = len(self._cmd(["git","ls-files","--modified","--deleted"],show=show))
    return f'{cnt}/files'

  def gtunstagedfiles(self,show:bool=True) -> str:
    """ Unstaged local files. """
    return self._cmdstr(["git","ls-files","--modified","--deleted"],show=show)

  def gtuncommitted(self,show=True) -> str:
    """ Uncommitted local changes. """
    branch = self._gtlocalbranch()
    files = self.gtuncommittedfiles(show=False)
    if not files: return "0/files"
    l = [os.path.getmtime(file) for file in files.split(os.linesep) if os.path.exists(file)]
    cnt = len(l)
    oldest = min(l)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - oldest)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{cnt}/files\n{branch}/br\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"

  def gtuncommittedfiles(self,show=True) -> str:
    """ Uncommitted local changes. """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"{branch}"],show=show)

  def gtuncommitteddiff(self,show=True) -> str:
    """ Uncommitted local changes. """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff",f"{branch}"],show=show)

  def gtremotebehind(self,show=True) -> str:
    """ remote..local """
    branch = self._gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}..{branch}"],show=show)
    if not a: return f"0/files\n{branch}/br"
    a = a[0].split(" ")
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    cnt = len(self.gtremotebehindfiles(show=False).split(os.linesep))
    return f"{cnt}/files {branch}/br\n{a[1]}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"

  def gtremotebehindfiles(self,show=True) -> str:
    """ remote..local """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/{branch}...{branch}"],show=show).strip()

  def gtremotebehinddiff(self,show=True) -> str:
    """ remote..local """
    branch = self._gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/{branch}...{branch}"],show=show).strip()

  def gtfetch(self,show=True) -> None:
    self._cmd(["git","fetch"],show=show)

# TODO
# Tag on local main branch, this tags the commit.
# git tag -a v1.2.3 -m "Release version 1.2.3"
# Push the tag to main, this triggers CI jobs,
# git push origin v1.2.3
# Get commit number, store in the version file.

  @classmethod
  def _main(cls,ap:argparse.ArgumentParser):
    """ Add extra parameters. """
    super()._main(ap)
    cls._add_argument(ap,'branch', help="Branch for gtbranch", cmds=["gtbranch"])
    cls._add_argument(ap,'url', help="URL of remote git project for gtsetremote",cmds=["gtsetremote","gtcreate"])
    cls._add_argument(ap,'pj', help="Project path",
                      cmds=["gtcreate","gtsetremote","gtadd","gtrebaseremote",
                            "gtrebasemain","gtpush","gttrackingremotebranch",
                            "gtbranch","gtlocalbranch","gtignorefile",
                            "gtignore"],optional=True)


if __name__ == "__main__":
  GtMake.main()      