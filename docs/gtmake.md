# git (gt) make

## New repo
```
make gtcreate --pj projectroot --repo url
```
wsroot: is a relative between ws.json and root.

path/ws.json: workspace is stored in this file and is added to git if path is
a git project.

url for the remote repo. A new repo must have an an empty remote repo, it is
important that the remote has no commits as this triggers an impossible merge
of main into an untracked repo. A new repo is linked with this url.

## Developer branch
```
make gtbranch --branch newfeature123
make gtuntracked; make gtadd
make gtunstaged; make gtadd
make gtmainahead; make gtrebasemain
make gtremoteahead; make gtrebaseremote
make gtuncommitted; make gtcommit
make gtremotebehind; make gtpush
```
A developer branch is best practise.

## Main branch
```
make gtuntracked; make gtadd
make gtunstaged; make gtadd
make gtremoteahead; make gtrebaseremote
make gtuncommitted; make gtcommit
```
A main branch is the default branch created by gtclone.