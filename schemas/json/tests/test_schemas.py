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

schemadir = os.path.dirname(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename):
    validator.validate_file(os.path.join(schemadir, filename), False, True)

def test_jsonschema(validator):
    validate(validator, os.path.join("extern", "json-schema.json"))

def test_mgijsonschema(validator):
    validate(validator, "mgi-json-schema.json")

def test_registry_resource_schema(validator):
    validate(validator, "registry-resource_schema.json")

def test_resmd_schema(validator):
    validate(validator, "res-md_schema.json")

def test_trans_schema(validator):
    validate(validator, "mgi-json-trans.json")




