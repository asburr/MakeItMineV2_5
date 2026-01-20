import os
import datetime
from makeitminev2_5.make import Make


class GtMake(Make):
  """ Platform independent recipies for a Makefile supporting GIT. Trunk
  based developement is working on temporary branches directly off main.
  """

  def _checkfile(self,file:str) -> str:
    return super()._checkfile(file)

  def _upversion(self,pj:str,version:str,oldversion:str) -> str:
    """ Update files containing version from BUILDVERSION.txt. """
    if os.path.exists(self.ci):
      self._sed(self.ci,'docker_image_version\s*:.*',f'docker_image__version: {version}')
    super._upversion(pj,version,oldversion)

  def _upversionneeded(self,version:str,oldversion:str) -> bool:
    """ Only up version when there are changes in the project """
    a = self._cmd(['git','diff','name-only','origin/main'],_show=True).split(os.linesep)
    return self.bv in a

  def _changes(self,pj:str) -> bool:
    """ Any changes to the project. """
    return super._changes(pj)

  def _workwarning(self) -> list:
    if self.gtlocalbranch() == "main":
      return ["warning (git): You are working on the main branch.\nHint: create a developer branch using 'gtbranch <branch name>'"]
    
  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return super()._work_align()+["l","l","l","l","l","l","l"]

  def _workTitles(self) -> list:
    """ Titles for work """
    return super()._workTitles()+[
      "gtsetupshow\ngtsetup",
      "gtuntracked\nlocal>local\ngtadd",
      "gtmainahead\nmain>local\ngtrebasemain",
      "gtremoteahead\nremote>local\ngtrebaseremote",
      "gtuncommitted\nlocal>remote\ngtdiff, gtpush",
      "gtremotebehind\nlocal>remote\ngtpush",
      "gtmainbehind\nremote>main\ngtrelease"]

  def _work(self) -> list:
    """ Gather project work """
    if not self.gtrepo(_show=False):
      return super()._work()+["not a repo","","","","","",""]
    email = self._cmdstr(["git","config","--global","user.email"],_show=False)
    if not email:
      return super()._work()+["no email","","","","","",""]
    self.gtfetch(_show=False)
    untracked = self.gtuntracked(_show=False)
    untracked = "" if untracked == "0/files" else untracked
    remote = self.gtremoteahead(_show=False)
    remote = "" if "0/files" in remote else remote
    main = self.gtmainahead(_show=False)
    main = "" if main == "n/a on main" or main == "0/files" else main
    mainbehind = self.gtmainbehind(_show=False)
    mainbehind = "" if mainbehind == "n/a on main" or mainbehind == "0/files" else mainbehind
    uncommited = self.gtuncommitted(_show=False)
    uncommited = "" if uncommited == "0/files" else uncommited
    remotebehind = self.gtremotebehind(_show=False)
    remotebehind = "" if remotebehind == "n/a on main" or remotebehind == "0/files" else remote
    return super()._work()+["",untracked,main,remote,uncommited,remotebehind,mainbehind]

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.gitignore=".gitignore"
    self.ci = ".gitlab-ci.yml"

  def gtignore(self) -> None:
    """ Create or append to .gitignore in current working directory. """
    paths = [f"{x}/" for x in self.ignorepaths()] + [".*/", ".*", "!.gitignore", "*.py[cod]"]
    if not os.path.exists(self.gitignore):
      print("creating {self.gitignore}")
      with open(self.gitignore,"w") as f:
        for s in paths:
          f.write(f"{s}{os.linesep}")
      return
    with open(self.gitignore,"r") as f:
      for line in f:
        try:
          paths.remove(line.strip())
        except Exception:
          pass
    with open(self.gitignore,"a") as f:
      for s in paths:
        print(f"Adding {s} to .gitignore")
        f.write(f"{s}{os.linesep}")
        
  def gtignorefile(self,file:str) -> None:
    """ Add file to git ignore. """
    if not os.path.exists(file):
      print(f"ERROR: No such file {file}")
      os._exit(1)
    filename = os.path.basename(file)
    if self._grep(self.gitignore,filename):
      print(f"INFO: {filename} in {self.gitignore}")
      return
    self._append(self.gitignore,filename)

  def gtlocalbranch(self) -> str:
    """ Name of the local branch """
    return self._cmd(["git","branch","--show-current"])[0]

  def gtclone(self,url:str,pj:str) -> None:
    """ clone repo
      :param url: URL for remote repo that is to be cloned.
      :param pj: local name for the repo being cloned.
    """
    if os.path.exists(pj):
      print(f"ERROR: {pj} already exists")
      os._exit(1)
    p = os.path.dirname(pj)
    if not os.path.exists(p):
      print(f"ERROR: porject root {p} must exists")
      os._exit(1)
    self._cmd(["git","clone",url,pj],_show=True)

  def gtbranch(self,branch:str,tag:str=None) -> None:
    """ Switch to a branch. Create branch locally if it does not exist.
        :param branch: the name of the branch
        :param tag: optional tag where the branch should start.
    """
    localbranch = self.gtlocalbranch()
    if localbranch == branch:
      print(f"already on {branch}")
      return
    self._cmd(["git","fetch"],_show=True)
    if branch in self._cmd(["git","branch","--list"],_show=True):
      self._cmd(["git","switch",branch],_show=True)
      self._cmd(["git","pull",branch],_show=True)
      return
    if branch == "main":
      print("Cannot create main branch")
      return
    if tag:
      tags = self._cmd(["git","tag"],_show=True)
      if tag not in tags:
        print(f"no tag called '{tag}', available tags {tags}")
        os._exit(1)
        self._cmd(["git","switch","-c",branch,tag],_show=True)
    else:
      self._cmd(["git","branch",branch],_show=True)
    self._cmd(["git","switch",branch],_show=True)

  def gttrackingremotebranch(self) -> bool:
    """ Does localbranch track a remote branch? """
    localbranch = self.gtlocalbranch()
    self._cmd(["git","fetch"],_show=True)
    for branch in self._cmd(["git","config","--get",f"branch.{localbranch}.remote"],_show=True,fail=False):
      if "origin" == branch: return True
    return False

  def gtpush(self,force:bool=False) -> None:
    """ Commit and push to remote branch
    :param force: without file checking
    """
    files = self.gtuncommittedfiles()
    if files:
      for file in files.split():
        if not force:
          r = self.checkfile(file)
          if r:
            print(r)
            return
      self._cmdInteractive(["git","commit","-a"],_show=True)
    localbranch = self.gtlocalbranch()
    if not self.gttrackingremotebranch():
      self._cmd(["git","branch",f"--track=origin/{localbranch}"],_show=True)
    if self.gtremoteaheadfiles():
      print("Error: remote is ahead of local.\nHint: gtrebaseremote")
      return
    # -u setups tracking between the new remote branch and the existing local branch
    self._cmd(["git","push","-u","origin",localbranch],_show=True)

  def gtrelease(self) -> None:
    """ TO TEST: release changes on remote branch into origin/main. """
    if self.gtuncommittedfiles():
      print("Error, commit local changes before merge")
      return
    branch = self.gtlocalbranch()
    if branch == "main":
      print("Error, on main branch and must be on a developer branch")
      return
    self._cmd(["git","checkout","main"],_show=True)
    self._cmd(["git","fetch"],_show=True)
    self._cmd(["git","pull"],_show=True)
    self._cmd(["git","merge","--no-ff",branch],_show=True)
    self._cmd(["git","push"],_show=True)

  def _release(self) -> None:
    """ release """
    super._release()
    branch = self.gtlocalbranch()
    if branch == "main":
      self.gtrelease()
    else:
      self.gtpush()

  def gtrebasemain(self) ->  None:
    """ TO TEST: rebase local branch with new changes on main. """
    work = self._cmd(["git","work"],_show=True)
    branch = self.gtlocalbranch()
    if [x for x in work if "interactive rebase in progress" in x]:
      print("INPROGRESS; rebase already in progress")
      self._cmdInteractive(["git","rebase","--continue"],_show=True)
      return
    if self.gtuncommittedfiles(_show=False):
      print("Error, commit local changes (gtuncommittedfiles) before merge")
      return
    if self.gtremoteahead(_show=False):
      print("ERROR gtrebasemain needed due to new changes on remote branch")
      return
    if branch == "main":
      print("ERROR use gtrebasemain when on main")
      return
    if not self.gtmainbehindfiles():
      print(f"Nothing to rebase, {branch} is up to date with main")
      return
    self._cmd(["git","fetch","origin"],_show=True)
    self._cmdInteractive(["git","merge","main"],_show=True)

  def gtrebaseremote(self) ->  None:
    """ rebase local branch with new changes on remote branch. """
    work = self._cmd(["git","status"],_show=True)
    if [x for x in work if "interactive rebase in progress" in x]:
      print("ERROR gtrebasemain in progress")
      return
    if self.gtuncommittedfiles(_show=False):
      print("ERROR gtpush local changes before merge")
      return
    self._cmdInteractive(["git","pull","origin","main"],_show=True)

  def gtadd(self) -> str:
    """ Add gtuntrackedfiles to git. """
    files = self.gtuntrackedfiles()
    if files: self._cmd(["git","add"]+files.split(os.linesep),_show=True)
    # files = self.gtunstagedfiles()
    # if files: self._cmd(["git","add"]+files.split(os.linesep),_show=True)

  def gtremoterepo(self,path:str) -> None:
    """ Initialize a local path as a REMOTE repo with trunk called "main" and
    repo is accessible by anybody.
    THIS IS A REMOTE REPO - Generally a remote repo is hosted on gitlab or
    github, but here the remote repo is created on the localhost.
    :param path: path where the remote repo will exist.
    """
    os.chdir(path)
    self._cmd(["git","init","--bare","--initial-branch=main","--shared=all"],_show=True)

  def gtrepo(self,_show:bool=True) -> bool:
    """ Check if current working directory is a git repo. """
    status = self._cmd(["git","status"],_show=_show,fail=False,stderr=True)
    return not self._substring("fatal: not a git repository",status)

  def gtsetupshow(self) -> None:
    """ Show the status of the local repo with user name and email. """
    if not self.gtrepo():
      print(f"{os.getcwd()} is not a repo, run gtsetup")
      os._exit(1)
    name = self._cmdstr(["git","config","--global","user.name"],_show=True)
    email = self._cmdstr(["git","config","--global","user.email"],_show=True)
    print(f"name='{name}' email='{email}'")
    if not email or not name:
      print("Setup local git, run gtsetup")
      os._exit(1)

  def gtsetup(self,location:str=None,name:str=None,email:str=None) -> None:
    """ Initialize CWD as a local repo and/or setup user name and email for
        local repo.
        :param location: Location of the remote repo which may be a URL or path.
        :param name: Name for the user of git.
        :param email: Email for the user of git.
    """
    if name: self._cmd(["git","config","--global","user.name",name],_show=True)
    if email: self._cmd(["git","config","--global","user.email",email],_show=True)
    if location:
      if self.gtrepo():
        print(f"ERROR: {self.cwd} is a git project")
        os._exit(1)
      self.gtignore()
      email = self._cmdstr(["git","config","--global","user.email"],_show=True)
      name = self._cmdstr(["git","config","--global","user.email"],_show=True)
      if not email or not name:
        print("ERROR: use gtinit to set email and name")
        os._exit(1)
      self._cmdInteractive(["git","init","--initial-branch","main","."],_show=True)
      self.gtadd()
      # Before push, must have at least one commit in the local history.
      self._cmd(["git","commit","-m","initial commit"],_show=True)
      # Add the path to the repository as a remote, origin being the standard
      # convention for a remote repo.
      self._cmd(["git","remote","add","origin",location],_show=True)
      self._cmd(["git","push","-u","origin","main"],_show=True)
    self._cmd(["git","config","pull.rebase","false"],_show=True)    

  def gtsetremote(self,url:str) -> None:
    """ Change set remote URL for a local repo.
    :param url: Location of the remote repo which may be a URL or path.
    """
    for u in self._cmd(["git","remote","get-url","origin","--all"],_show=True):
      if u != url:
        print(f"different url in .git/config please edit to delete the url {u}")
        os._exit(1)
      else:
        print(f"{url} already in .git/config wont readd")
        return
    self._cmd(["git","remote","set-url","--add","origin",url],_show=True)

  #   three dot notation i.e. origin/branch...origin/main
  #   -=================-
  #   The three dots limits the difference to the work done on the branch on
  #   the right of the dots since the common ancestor with the branch on the
  #   left. In this case, the remote branch is on the right so it's _showing
  #   changes in this branch, and the local branch is on the left so it
  #   linmited changes to the point at which the local branched from the
  #   remote.
  #   Therefore, it's _showing changes in remote since local branched.
  #   Note the two dot notation. When used for diff, the two dots
  #   does not limited the difference but _shows differences between the
  #   heads of both branches. Which is not what we want here, and three dots
  #   is what we need for diff.
  #   Also note that the dot notation has opposite behaviour with git log.
  #   two dot notation  i.e. origin/branch..origin/main.
  #   -===============-
  #   Note the two dots. When used for log, the two dots limits the list of
  #   commits to the work done on the right hand branch from the common
  #   ancestor with the branch on the left.
  #   Note the three dots. When used for log, the three dots does not
  #   limit the commit to any branch but _shows all of the comments on both
  #   branches since the common ancestor. Which is not want we want here,
  #   and two dots is what we need for log.
  #   Also note that the dot notation has opposite behaviour with git diff.
  
  def gtmainahead(self,_show:bool=True) -> str:
    """ remote..main """
    branch = self.gtlocalbranch()
    if branch == "main": return "n/a on main"
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}..origin/main"],_show=_show).split("\n")[0].split(" ")
    if not a[0]: return f"0/files\n{branch}/br"
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    cnt = len(self.gtmainaheadfiles(_show=False).split(os.linesep))
    return f"{cnt}/files\n{branch}/br\n{a[1]}/uid {dd:>02d}:{hh:>02d}:{mm:>02d}/age"

  def gtmainaheadfiles(self,_show=True) -> str:
    """ remote..main """
    branch = self.gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/{branch}...origin/main"],_show=_show)

  def gtmainaheaddiff(self,_show=True) -> str:
    """ remote..main """
    branch = self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/{branch}...origin/main"],_show=_show)

  def gtmainbehind(self,_show=True) -> str:
    """ main..remote """
    branch = self.gtlocalbranch()
    if branch == "main": return "n/a on main"
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/main..origin/{branch}"],_show=_show).split("\n")[-1].split(" ")
    if not a: return f"0/files\n{branch}/br"
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    remote = a[1].split("/")[-1]
    cnt = len(self.gtmainbehindfiles(_show=False).split(os.linesep))
    return f'{cnt}/files\n{branch}/br\n{remote}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age'

  def gtmainbehindfiles(self,_show=True) -> str:
    """ Branch commits not released to main branch. """
    branch=self.gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/main...origin/{branch}"],_show=_show)

  def gtmainbehinddiff(self,_show=True) -> str:
    """ Branch commits not released to main branch. """
    branch=self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/main...origin/{branch}"],_show=_show)

  def gtdiff(self,_show=True) -> str:
    """ Local changes regardless of whether they are committed or uncommitted. """
    branch=self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/{branch}"],_show=_show)

  def gtremoteahead(self,_show=True) -> str:
    """ local..remote. """
    branch = self.gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"{branch}..origin/{branch}"],_show=_show)
    if not a: return f"0/files\n{branch}/br"
    a=a[-1].split(" ")
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]))
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    remote = a[1].split("/")[-1]
    cnt = len(self.gtremoteaheadfiles(_show=False).split(os.linesep))
    return f'{cnt}/files\n{branch}/br\n{remote}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age'

  def gtremoteaheadfiles(self,_show=True) -> str:
    """ local...remote. """
    branch=self.gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"{branch}...origin/{branch}"],_show=_show)

  def gtremoteaheaddiff(self,_show=True) -> str:
    """ local...remote. """
    branch=self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"{branch}...origin/{branch}"],_show=_show)

  def gtuntracked(self,_show:bool=True) -> str:
    """ Untracked local files. """
    files = self._cmd(["git","ls-files","--others","--exclude-standard"],_show=_show)
    if not files: return "0/files"
    files = [os.path.getmtime(file) for file in files if os.path.exists(file)]
    cnt = len(files)
    oldest = min(files)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - oldest)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f'{cnt}/files\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age'

  def gtuntrackedfiles(self,_show:bool=True) -> str:
    """ Untracked local files. """
    return self._cmdstr(["git","ls-files","--others","--exclude-standard"],_show=_show)

  def gtunstaged(self,_show:bool=True) -> str:
    """ Unstaged changes. """
    cnt = len(self._cmd(["git","ls-files","--modified","--deleted"],_show=_show))
    return f'{cnt}/files'

  def gtunstagedfiles(self,_show:bool=True) -> str:
    """ Unstaged local files. """
    return self._cmdstr(["git","ls-files","--modified","--deleted"],_show=_show)

  def gtuncommitted(self,_show:bool=True) -> str:
    """ Uncommitted local changes; excluding deleted files. """
    branch = self.gtlocalbranch()
    files = self.gtunstagedfiles(_show=_show)
    files = self.gtuncommittedfiles(_show=_show) + (files if files else "")
    if not files: return "0/files"
    addfiles = [os.path.getmtime(file) for file in files.split(os.linesep) if os.path.exists(file)]
    if not addfiles: return "0/files"
    cnt = len(addfiles)
    oldest = min(addfiles)
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - oldest)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    return f"{cnt}/files\n{branch}/br\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"

  def gtuncommittedfiles(self,_show=True) -> str:
    """ Uncommitted local changes. """
    branch = self.gtlocalbranch()
    unstaged = self._cmd(["git","ls-files","--modified","--deleted"],_show=_show)
    unstaged = unstaged if unstaged else ""
    uncommitted = self._cmd(["git","diff","--name-only",f"{branch}"],_show=_show)
    r = set(unstaged)
    if uncommitted: r |= set(uncommitted)
    return "\n".join(r)

  def gtuncommitteddiff(self,_show=True) -> str:
    """ Uncommitted local changes. """
    branch = self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"{branch}"],_show=_show)

  def gtremotebehind(self,_show=True) -> str:
    """ remote..local """
    branch = self.gtlocalbranch()
    a = self._cmd(["git","log","--date=unix","--pretty=format:%ad %an",f"origin/{branch}..{branch}"],_show=_show)
    if not a: return f"0/files\n{branch}/br"
    a = a[0].split(" ")
    d = datetime.timedelta(seconds=datetime.datetime.now().timestamp() - int(a[0]) if a else 0)
    dd = d.days
    hh = d.seconds//3600
    mm = (d.seconds//60)%60
    cnt = len(self.gtremotebehindfiles(_show=False).split(os.linesep))
    return f"{cnt}/files {branch}/br\n{a[1]}/uid\n{dd:>02d}d:{hh:>02d}H:{mm:>02d}M/age"

  def gtremotebehindfiles(self,_show=True) -> str:
    """ remote..local """
    branch = self.gtlocalbranch()
    return self._cmdstr(["git","diff","--name-only",f"origin/{branch}...{branch}"],_show=_show).strip()

  def gtremotebehinddiff(self,_show=True) -> str:
    """ remote..local """
    branch = self.gtlocalbranch()
    return self._cmdstr(["git","diff",f"origin/{branch}...{branch}"],_show=_show).strip()

  def gtfetch(self,_show=True) -> bool:
    return self._cmd(["git","fetch"],fail=False,_show=_show)

  def gttag(self) -> None:
    """ Adds a local lightweight tag (one without a comment) to the last commit.
      Lightweight tags remain local and are not pushed to the remote branches.
    """
    self._cmd(["git","tag",self.version()])