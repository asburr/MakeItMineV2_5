from makeitminev2_5.make import Make
from makeitminev2_5.dkmake import DkMake
from makeitminev2_5.gtmake import GtMake
from makeitminev2_5.pymake import PyMake
from makeitminev2_5.djmake import DJMake

class PjMake(DJMake,GtMake,PyMake,DkMake,Make):
  """ Project make using other makes. """
  pass


if __name__ == "__main__":
  PjMake.main()