import inspect
import argparse
import re
from makeitminev2_5.makeutils import _MakeUtils


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


def  ap_decorator_func(rootcls,func,cls):
  f""" Helper. {ap_decorator_doc} """
  if not getattr(rootcls, "main_p", None):
    cls.main_p = argparse.ArgumentParser(
      description="makeitmine",
      formatter_class=argparse.RawDescriptionHelpFormatter)
    cls.main_p.add_argument("--stacktrace","-s",action="store_true",help="Stacktrace on exit")
    cls.main_s_p = rootcls.main_p.add_subparsers(dest="command", help="commands")
    cls.main_s_p_parser = {}
  class_name = func.__qualname__.split('.')[0]
  if class_name != cls.__name__:
    """ subclasses dont add parent methods unless it is overloaded. """
    return
  cn = cls._name
  cfullname = cls._fullname
  # print(f"func={func.__qualname__} scope={cn}")
  if cn.startswith("_"): return
  p = rootcls.main_s_p_parser.get(cn,None)
  active_default = getattr(cls,"_active_default")
  if not p:
    if cls._getpreference(cn,active_default):
      p = rootcls.main_s_p.add_parser(cn,
                                      formatter_class=argparse.RawTextHelpFormatter,
                                      help=f"{cfullname} active, see <makeitmine> {cn} --help",
                                      description=cls.__doc__)
      p = p.add_subparsers(help='commands')
    else:
      p = rootcls.main_s_p.add_parser(cn,
                                      formatter_class=argparse.RawTextHelpFormatter,
                                      help=f"{cfullname} not active, see <makeitmine> mk activate {cn}",
                                      description=f"{cls.__doc__} - not active; make activate {cn}")
    rootcls.main_s_p_parser[cn] = p
  if not cls._getpreference(cn,active_default):
    return
  n = func.__name__
  doc = func.__doc__
  if not doc: return
  description=re.sub("\n\s*:param .*","",doc) if doc else ""
  p = p.add_parser(n,
                   formatter_class=argparse.RawDescriptionHelpFormatter,
                   help=doc,description=description)
  p.set_defaults(func=func)
  p.set_defaults(cls=cls)
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
  for subcls in [subcls for subcls in inspect.getmro(cls) if subcls.__name__ not in ["ABC","_MakeUtils","object"]]:
    for n in dir(subcls):
      if n.startswith("_"): continue
      func = getattr(subcls,n,None)
      if func is None: continue
      if not callable(func): continue
      ap_decorator_func(cls,func,subcls)
    

def ap_decorator_runcmd(cls):
  """ A function to be called after ab_decorator_main to run the command """
  # m = cls()
  if getattr(cls,"main_p",None) is None: return
  a, unknown = cls.main_p.parse_known_args()
  d = a.__dict__
  _MakeUtils.stacktrace = d["stacktrace"]
  del d["stacktrace"]
  kwargs={}
  it = iter(unknown)
  for (k,v) in zip(it,it):
    kwargs[k[2:]] = v
  if not hasattr(a, 'func'):
    _MakeUtils.stop(cls.main_p.print_help())
  d = {k:v for k,v in d.items() if k not in ["cls","command","func"] and v is not None}
  m = a.cls()
  print(a.func.__name__)
  r = getattr(m,a.func.__name__)(**(d | kwargs))
  if r is not None: print(r)
