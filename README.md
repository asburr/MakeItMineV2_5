# MakeItMine (MIM)
MIM provides build automation called targets for software development workflows.
## git targets
Git Trunk Based Dev with developer branches but support without developer branches.

Targets: gtsetup(location,name,email), gtadd(), gtrebaseremote(), gtdiff(),
gtpush(), gtrelease().

Tasks for developer branch: gtbranch, gtrebasemain
## Docker targets
Multi-Stage Dockerfile. Host Volume Mounting docker-compose for development.
Env Driven docker-compose.

Targets: dkbuild, dkup, dklogs, dkdown
## Python targets
Python development using Poetry in the Package-Mode, using Dependency-Groups
to manage the separation of dev and prod dependencies.

Targets: pyinstall(package,version), pyuninstall(package), pypackage(),
pyunittest(), pye2etest().
## Workspace targets
Workspace is a collection of local projects being changed at the sametime.

Targets: wsset(ws), ws(), wsadd(pj,path), wsrm(pj), wswork(pj),
wsrun(cmd,pj,args,kwargs)
## Getting Started
### Dependencies
MIM has been tested with Linux distributions, Ubuntu and Debian.
### Installing
Clone the repo from https://github.com/asburr/MakeItMineV2_5.
### Executing program
Run the script MakeItMine.sh.
```
alias MIM=~/project/MakeItMineV2_5/MakeItMine.sh
MIM --help
```
### Testing MIM
```
MIM pye2etest
```
## Add a workflow
Workflows inherit an abstract framework from Make in make.py.
Abstraction: _ignorepaths, _checkfile(file), _workTitles(), _work(),
_work_align(), wspjpath().
### Common utilities
Workflows also inherit utilities from MakeUtils in makeutils.py.
utils: _touch(p), _sed(fn,pattern,s), _grep(fn,pattern), _append(fn,line),
_cmd(cmd,_show,fail,stderr), _cmdstr(cmd,_show,fail,stderr),
_cmdInteractive(cmd,fail,_show), _rebuild_target(target,dependencies)
### Adding methods
Methods starting with underscore are not intended to be called by a user and are
hidden from the CLI. Other methods are automatically added to the CLI as a user
command but only if the method has a docstring, methods without a docstring
are not included in the CLI. Parameters starting with underscore are also not
intended to be set by the user through the CLI. Other paramenters are
automatically added as parameters to the command. Standard ":param" help is
shown by the CLI help. For example,
```
class GtMake(Make):
  """ Platform independent recipies for a Makefile supporting GIT. Trunk
  based developement is working on temporary branches directly off main.
  """

  def gtbranch(self,branch:str) -> None:
    """ Switch to a branch. Create branch locally if it does not exist.
        :param branch: the name of the branch
    """
``` 
### ignorepaths
List paths that this workflow knows to _ignorepaths. Call super()._ignorepaths().
```
  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return []
```
### checkfile
Check the syntax of a file in _checkfile. Call super()._checkfile().
```
  @abstractmethod
  def _checkfile(self,file:str) -> bool:
    """ Check the syntax and semantics in a file """
    if file.endswith(".json"):
      with open(file,"r",encoding='utf-8') as f:
        try:
          json.load(f)
        except Exception as e:
          print(f"{file} bad json syntax error is {e}")
          return False
    return True
```
### tasks
Provide a summary of all tasks found in the flow, including pending tasks
and completed tasks. Describe each task in the titles returned by
_workTitles, these descriptions should identify the CLI command that shows the
status as well as the CLI command that does the tasks itself. The status
of the task is reported in _work, completed tasks must be report an
empty string. The alignment of the status is either left (l) or right(r)
or center (c). There must be a title and status-string and alignment-string
for each task.
```
  @abstractmethod
  def _workTitles(self) -> list:
    """ Titles for work """
    return []

  @abstractmethod
  def _work(self) -> list:
    """ Gather project work """
    return []

  @abstractmethod
  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return []
```
### Workspce project path
Flows that are able to locate a local-repo may implement wspjpath
to return the path to the local-repo associated with the project name.
``` 
  @abstractmethod
  def wspjpath(self,pj:str) -> str:
    """ Project is part of the users workspace and project is
    available locally at the returned path.
    :param pj: project name.
    """
    return None
```
## Version History
* 0.0.1
    * Pre-Release demonstration of the concept.
## License
This project is licensed under the MIT License - see the LICENSE file for details
