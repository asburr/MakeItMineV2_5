import inspect
import argparse
import os


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
  bool: {"action":"store_false"},
  int: {"type":int},
  str: {},
  list[int]: {"type":int,"nargs":"*"},
  list[str]: {"nargs":"*"},
  list[bool]: {"action":"store_false","nargs":"*"}
}


def  ap_decorator_func(func,cls):
  f""" Helper. {ap_decorator_doc} """
  if not getattr(cls, "parser_g", None):
    cls.parser_g = argparse.ArgumentParser(description="makeitmine")
    cls.subparsers_g = cls.parser_g.add_subparsers(dest="command", help="commands")
    cls.subparser_g = {}
  n = func.__name__
  p = cls.subparser_g.get(n,None)
  if p:
    raise Exception(f"{func.__name__} already has an subparser")
  p = cls.subparsers_g.add_parser(n,help=func.__doc__,description=func.__doc__)
  cls.subparser_g[n] = p
  p.set_defaults(func=func)
  params = {k:v for k,v in inspect.signature(func).parameters.items()
            if k != 'self' and k != 'args' and k != 'kwargs'
            }
  for name, param in params.items():
    if name.startswith("_"): continue
    type_hint = param.annotation
    if type_hint is inspect.Parameter.empty:
      raise Exception(f"ERROR: Missing type hint for {n}({name})")
    kwargs = __d.get(type_hint,None)
    if kwargs is None:
      raise Exception(f"ERROR: no support for {n}({name}:{type_hint})")
    if param.default is not inspect.Parameter.empty:
      name = f"--{name}" # Default value means parameter is optional.
    p.add_argument(name,**kwargs)


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
    ap_decorator_func(func,cls)

def ap_decorator_runcmd(cls):
  m = cls()
  a, unknown = cls.parser_g.parse_known_args()
  kwargs={}
  it = iter(unknown)
  for (k,v) in zip(it,it):
    kwargs[k[2:]] = v
  if not hasattr(a, 'func'):
    cls.parser_g.print_help()
    os._exit(1)
  d = vars(a).copy()
  del d["command"]
  del d["func"]
  r = getattr(m,a.func.__name__)(**(d | kwargs))
  if r is not None: print(r)