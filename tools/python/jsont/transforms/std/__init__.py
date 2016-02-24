"""
transforms from the standard module.   

This module provides implimentations for required transforms and transform types
"""
import os 

MODULE_NAME = __name__

from .types import *
from .native import *

# the mapping of "$type" labels to Transform classes used by Engine to 
# instantiate different Transform types
#
types = { "literal": Literal, 
          "stringtemplate": StringTemplate, 
          "native": Native,
          "map": Map,
          "foreach": ForEach,
          "json": JSON,
          "extract": Extract,
          "apply": Apply,
          "callable": Callable
          }

# load in stylesheet-based definitions 

MOD_STYLESHEET_FILE = "ss.json"

ssfile = os.path.join(os.path.dirname(__file__), MOD_STYLESHEET_FILE)
with open(ssfile) as fd:
    MOD_STYLESHEET = jsp.load(fd)
del ssfile

# load the module's initial context data.  The defaults are specified in 
# context.py for documentation purposes; however, values set wihtin the 
# stylesheet file will take precedence.

from .context import def_context

MOD_CONTEXT = ScopedDict(def_context)
MOD_CONTEXT.update(MOD_STYLESHEET.get('context',{}))
MOD_STYLESHEET['context'] = MOD_CONTEXT

