import os
from makeitminev2_5.make import Make
from makeitminev2_5.makeutils import MakeUtils


class DJMake(Make,MakeUtils):
  """ Platform independent recipies for a Makefile supporting a Django project.
  """

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.x = os.path.join("docker","Dockerfile")


if __name__ == "__main__":
  DJMake.main()
