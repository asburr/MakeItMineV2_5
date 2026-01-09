#!/bin/bash
"exec" "$(poetry --directory $(realpath $(dirname ${BASH_SOURCE[0]})) env info --path )/bin/python" "$0" "$@"
#"exec" "poetry" "--directory" "$(realpath $(dirname ${BASH_SOURCE[0]}))" "run" "python" "$0" "$@"
import sys
import os
# Dont need to add script-dir due running poetry from script-dir in exec above.
#sys.path.insert(0, os.path.dirname(__file__))
from makeitminev2_5.pjmake import PjMake
PjMake.main()
