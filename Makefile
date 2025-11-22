
ifeq ($(MIM),)
  $(error $$MIM must be defined as the path to the MakeItMine project)
endif
MAKE:=$(MIM)/venv/bin/python -m MakeItMineV2_5.pjmake


BUILDVERSION.txt:
	$(MAKE) BUILDVERSION.txt

README.txt:
	$(MAKE) README.txt

create_Dockerfile:
	$(MAKE) create_Dockerfile

dkbuild:
	$(MAKE) dkbuild

dkcheck:
	$(MAKE) dkcheck

dkdown:
	$(MAKE) dkdown

dkimages:
	$(MAKE) dkimages

dkpull:
	$(MAKE) dkpull

dkrun:
	$(MAKE) dkrun

dkup:
	$(MAKE) dkup

genmakefile:
	$(MAKE) genmakefile

gtadd:
	$(MAKE) gtadd

gtbranch:
	$(MAKE) gtbranch

gtcreate:
	$(MAKE) gtcreate

gtfetch:
	$(MAKE) gtfetch

gtignore:
	$(MAKE) gtignore

gtlocalbranch:
	$(MAKE) gtlocalbranch

gtmainahead:
	$(MAKE) gtmainahead

gtmainaheaddiff:
	$(MAKE) gtmainaheaddiff

gtmainaheadfiles:
	$(MAKE) gtmainaheadfiles

gtmainbehind:
	$(MAKE) gtmainbehind

gtmainbehinddiff:
	$(MAKE) gtmainbehinddiff

gtmainbehindfiles:
	$(MAKE) gtmainbehindfiles

gtpush:
	$(MAKE) gtpush

gtrebasemain:
	$(MAKE) gtrebasemain

gtrebaseremote:
	$(MAKE) gtrebaseremote

gtrelease:
	$(MAKE) gtrelease

gtremoteahead:
	$(MAKE) gtremoteahead

gtremoteaheaddiff:
	$(MAKE) gtremoteaheaddiff

gtremoteaheadfiles:
	$(MAKE) gtremoteaheadfiles

gtremotebehind:
	$(MAKE) gtremotebehind

gtremotebehinddiff:
	$(MAKE) gtremotebehinddiff

gtremotebehindfiles:
	$(MAKE) gtremotebehindfiles

gtsetremote:
	$(MAKE) gtsetremote

gttrackingremotebranch:
	$(MAKE) gttrackingremotebranch

gtuncommitted:
	$(MAKE) gtuncommitted

gtuncommitteddiff:
	$(MAKE) gtuncommitteddiff

gtuncommittedfiles:
	$(MAKE) gtuncommittedfiles

gtuntracked:
	$(MAKE) gtuntracked

gtuntrackedfiles:
	$(MAKE) gtuntrackedfiles

init.py:
	$(MAKE) init.py

name:
	$(MAKE) name

prod_venv:
	$(MAKE) prod_venv

project.toml:
	$(MAKE) project.toml

pybuild:
	$(MAKE) pybuild

pycheck:
	$(MAKE) pycheck

pyinit.py_path:
	$(MAKE) pyinit.py_path

pyrequirements:
	$(MAKE) pyrequirements

pyversion:
	$(MAKE) pyversion

status:
	$(MAKE) status

upversion:
	$(MAKE) upversion

venv:
	$(MAKE) venv

version:
	$(MAKE) version

