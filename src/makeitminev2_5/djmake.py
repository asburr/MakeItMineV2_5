import os
from makeitminev2_5.abc_make import _ABCMake


class DJMake(_ABCMake):
  """ Platform independent recipies for a Makefile supporting a Django project.
  """

  _name = "django"
  _fullname = "django"
  _active_default = False

  
  def __init__(self,**kwargs):
    super().__init__(**kwargs)
    self.x = os.path.join("docker","Dockerfile")
