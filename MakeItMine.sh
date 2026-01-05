#!/bin/bash
"exec" "poetry" "run" "python" "$0" "$@"
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from makeitminev2_5.pjmake import PjMake
PjMake.main()
