""" The Make recipe framework. Recipes inherit from ABCMake and implement the methods. """
import json
import os
from pathlib import Path
from abc import ABC, abstractmethod
from makeitminev2_5.ap_decorator import ap_decorator_main, ap_decorator_runcmd


class _ABCMake(ABC):

  _name = "_abc"
  _fullname = "_abcmake"

  @abstractmethod
  def _release(self) -> None:
    """ Release a project. """
    pass

  @abstractmethod
  def _ignorepaths(self) -> list:
    """ List of visible paths to ignore. """
    return []

  @abstractmethod
  def _checkfile(self,file:str) -> str:
    """ Check the syntax and semantics in a file """
    if file.endswith(".json"):
      with open(file,"r",encoding='utf-8') as f:
        try:
          json.load(f)
        except Exception as e:
          return f"{file} bad json syntax error is {e}"

  @abstractmethod
  def _upversionneeded(self) -> bool:
    """ Is up version needed. """
    pass

  @abstractmethod
  def _upversion(self,version:str,oldversion:str) -> None:
    """ Up version the project. """
    pass

  @abstractmethod
  def _workTitles(self) -> list:
    """ Titles for work """
    return []

  @abstractmethod
  def _work(self) -> list:
    """ Gather project work """
    return []

  @abstractmethod
  def _work_align(self) -> list:
    """ Gather table alignment as "l" "r" "c" """
    return []

  preferences = os.path.join(Path.home(),".makeitmine.json")

  @classmethod
  def main(cls):
    ap_decorator_main(cls)
    ap_decorator_runcmd(cls)

  @classmethod
  def _getpreference(cls,key:str,default:any=False) -> any:
    """ Preferences are stored in home/.makeitmine.json
    :param key: Key to preference
    :param default: default value if no value found, default can be any type.
    :return: value for the key or None.
    """
    j = {}
    if os.path.exists(cls.preferences):
      try:
        with open(cls.preferences,"r") as f:
          j = json.load(f)
          v = j.get(key,None)
          if v != None:
            return v
      except Exception as e:
        print(f"ERROR: {cls.preferences} is corrupt {e}")
    with open(cls.preferences,"w") as f:      
        j[key] = default
        json.dump(j,f)
    return default

  @classmethod
  def _setpreference(cls,key:str,value:str) -> None:
    """ Preferences are stored in home/.makeitmine.json
    :param key: Key to preference
    :param value: Value for key.
    """
    if os.path.exists(cls.preferences):
      with open(cls.preferences,"r") as f:
        j = json.load(f)
        j[key]=value
      with open(cls.preferences,"w") as f:
        json.dump(j,f)
    else:
      with open(cls.preferences,"w") as f:
        json.dump({key:value},f)

