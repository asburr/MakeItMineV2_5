# make
## workflow
* workspace
  * add project
```
make workspace --ws wsroot --add projectroot
```
  * remove project 
```
make workspace --ws wsroot --remove projectroot
```
* build and test
```
make --ws wsroot done
make --pj projectroot done
```
  * build
```
make --ws wsroot done
make --pj projectroot done
```
  * test
```
make --ws wsroot test
make --pj projectroot test
```
  * build and test and release
```
make --ws wsroot release
make --pj projectroot release
```
  * status
```
make --ws wsroot status
make --pj projectroot status
```
## Install
* Makefile
  * from MakeItMine project
```
cd mimroot
export MIM=${PWD}
make --pj projectroot cmd
```
  * from target project.
```
cd mimroot
export MIM=${PWD}
export MAKE="make -f ${MIM}/Makefile"
cd projectroot
${MAKE} cmd
```
* makeitmine tool
```
cd make-root
export MIM=${PWD}
make MakeItMine
makeitmine [-pj projectroot] cmd
```