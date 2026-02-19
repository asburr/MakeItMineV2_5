import inspect
import argparse
import re
import sys
import os
from makeitminev2_5.makeutils import MakeUtils


ap_decorator_doc = """
    Adding command options for parameters with type hint and the
    following hint types are supported: bool, int, str, list[int], list[str],
    list[bool].
    Default values makes the option optional which means "--" is added to the
    option name.
    No default makes the parameter not optional i.e. "--" is not added to the
    option name.
"""


__d = {
  bool: {"action":"store_true"},
  int: {"type":int},
  str: {},
  list[int]: {"type":int,"nargs":"*"},
  list[str]: {"nargs":"*"},
  list[bool]: {"action":"store_true","nargs":"*"}
}


def  ap_decorator_func(func,cls):
  f""" Helper. {ap_decorator_doc} """
  if not getattr(cls, "parser_g", None):
    cls.parser_g = argparse.ArgumentParser(description="makeitmine")
    cls.parser_g.add_argument("--stacktrace",action="store_true",help="Stacktrace on exit")
    cls.subparsers_g = cls.parser_g.add_subparsers(dest="command", help="commands")
    cls.subparser_g = {}
  n = func.__name__
  doc = func.__doc__
  if not doc: return
  p = cls.subparser_g.get(n,None)
  if p:
    raise Exception(f"{func.__name__} already has an subparser")
  description=re.sub("\n\s*:param .*","",doc) if doc else ""
  p = cls.subparsers_g.add_parser(n,help=doc,description=description)
  cls.subparser_g[n] = p
  p.set_defaults(func=func)
  params = {k:v for k,v in inspect.signature(func).parameters.items()
            if k != 'self' and k != 'args' and k != 'kwargs'
            }
  for name, param in params.items():
    if name.startswith("_"): continue
    m=re.search(f".*:param {name}: (.*)$",doc,flags=re.MULTILINE)
    pdoc = ""
    if m: pdoc = m.group(1)
    type_hint = param.annotation
    if type_hint is inspect.Parameter.empty:
      raise Exception(f"ERROR: Missing type hint for {n}({name})")
    kwargs = __d.get(type_hint,None)
    if kwargs is None:
      raise Exception(f"ERROR: no support for {n}({name}:{type_hint})")
    if param.default is not inspect.Parameter.empty:
      name = f"--{name}" # Default value means parameter is optional.
    p.add_argument(name,help=pdoc,**kwargs)

class ap_decorator_class:
    f"""
    A decorator to register a function as a command with argparse.
    {ap_decorator_doc}
    """
    def __init__(self):
      pass

    def __call__(self, func):
      ap_decorator_func(func,ap_decorator_class)
      return func


ap_decorator = ap_decorator_class()


def ap_decorator_main(cls):
  """ A function to be called after the cls is defined so it exists for dir()
  to work. Adds all methods of class to argsparse on class.
  """
  for n in dir(cls):
    if n.startswith("_"): continue
    func = getattr(cls,n)
    if not callable(func): continue
    ap_decorator_func(func,cls)

def ap_decorator_runcmd(cls):
  """ A function to be called after ab_decorator_main to run the command """
  m = cls()
  a, unknown = cls.parser_g.parse_known_args()
  d = a.__dict__
  MakeUtils.stacktrace = d["stacktrace"]
  del d["stacktrace"]
  kwargs={}
  it = iter(unknown)
  for (k,v) in zip(it,it):
    kwargs[k[2:]] = v
  if not hasattr(a, 'func'):
    MakeUtils.stop(cls.parser_g.print_help())
  d = {k:v for k,v in d.items() if k not in ["command","func"] and v is not None}
  r = getattr(m,a.func.__name__)(**(d | kwargs))
  if r is not None: print(r)
