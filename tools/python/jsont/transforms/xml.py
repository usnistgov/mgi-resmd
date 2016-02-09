"""
transforms for creating XML from JSON data
"""
import os, json, copy, re

from ..exceptions import *
from ..base import Transform, ScopedDict

MODULE_NAME = __name__
TRANSFORMS_PKG = __name__.rsplit('.', 1)[0]

