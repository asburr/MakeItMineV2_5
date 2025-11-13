from MakeItMineV2_5.make import Make
from MakeItMineV2_5.dkmake import DkMake
from MakeItMineV2_5.gtmake import GtMake
from MakeItMineV2_5.pymake import PyMake

class PjMake(GtMake,PyMake,DkMake,Make):
  """ Project make using other makes. """
  pass


if __name__ == "__main__":
  PjMake.main()