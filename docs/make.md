# make
## workflow
* Managing a workspace.
Workspaces are created and added to using "wsadd". Remove using "wsrm".
Workspaces are displayed using "ws".
```
wsadd [--ws ws.json] --pj projectname --path projectroot
wsrm [--ws ws.json] --pj projectname
ws [--ws ws.json]
```
Note: the defaultname is ws.json.
* Developing the project.
Projects are built and tested. Testing will also build if it was not done prior.
```
build
test
```
note: build ordering is automatically decided when building multiple projects
using the workspace.
* Releasing a change.
Releasing a Project will also build and test if needed.
Release supports any version including the Semanic Versioning as
shown below.
Release automatically increments the lowest level, the patch level when using
SemVer i.e. N.N.N+1 if no options are provided.
A new version can be specified using the --version option.
Release support SemVer options which are --major and --minor.
--major increments the major version and sets minor and patch levels are zero
i.e. N+1.0.0.
--minor increments the minor version and the patch levels are zero i.e N.N+1.0
```
release --version <major>.<minor>.<patch>
release [--major] # major+1,minor=0,patch=0
release [--minor] # major.minor+1,patch=0
release # patch+1
```
note: a release order is automatically decided if releasing multiple projects
using the workspace.
* Using the workspace
The workspace can be used to run the the command: build, test, upversion,
and release.
* --ws option, run the command for all Projects in the Workspace.
* --ws and --pj options, run the command for an particular project.
* --path option, run the command for a particular project.
* No option, run the command for the project in the current working dir.
```
--ws ws.json 
--ws ws.json --pj projectname
--path projectroot
<no options runs in project's path>
```
## Install
Clone this project, then run the shell script called MakeItMine.sh from
whereever you like.
```
cd mimroot
./MakeItMine.sh <cmd> [<options>]
```
## About MakeItMine
### Workflow hooks
There is a Make class for the workflows of git and Python and Docker and Django.
The framework is in make.py and provides ws, wsadd, wsrm, build, test, and
release as previously described. Workflows override the following methods to
add their behaviour an action.
'''
_newfile(self,file:str) """ "Created a new file that needs to be saved to the project. """
_build(self,pj:str) """ build the project. """
_test(self,pj:str) """ test """
_upversionneeded(self) -> bool """ Is up version needed. """
_release(self,pj:str) """ Release a project. """


'''
Workflow utils
'''
_run(self,cmd,pj:str=None,ws:str=None) -> any
""" Run a command for projects in workspace and individual project. """

'''