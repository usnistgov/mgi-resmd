# import pytest
from __future__ import with_statement
import json, os, sys, pytest, shutil
from cStringIO import StringIO

try:
    # prefer version in PYTHONPATH, if it exists
    import xjs
except ImportError:
    xjsmoddir = os.path.join(os.path.dirname(os.path.dirname(
                             os.path.dirname(os.path.dirname(__file__)))),
                             "tools", "python")
    sys.path.append(xjsmoddir)
    import xjs

from xjs.validate import ExtValidator

schemadir = os.path.join(
   os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                        "schemas", "json")
exdir = os.path.dirname(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename, strict=True):
    validator.validate_file(os.path.join(exdir, filename), False, strict)

def test_ipr(validator):
    validate(validator, "ipr.json", False)

