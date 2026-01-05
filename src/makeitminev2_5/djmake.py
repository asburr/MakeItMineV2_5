import os
from makeitminev2_5.make import Make


class DJMake(Make):
  """ Platform independent recipies for a Makefile supporting a Django project.
  """
  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return super()._ignorepaths()

  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.x = os.path.join("docker","Dockerfile")


if __name__ == "__main__":
  DJMake.main()
