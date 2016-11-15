"""
This suite tests the validation of schemas that use the enhanced documentation.
"""
# import pytest
from __future__ import with_statement
import json, os, pytest, shutil
import jsonschema as jsch
from cStringIO import StringIO

from . import Tempfiles
import xjs.validate as val
import xjs.schemaloader as loader

schemadir = os.path.join(
   os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                        "schemas", "json")
mgi_json_schema = os.path.join(schemadir, "mgi-json-schema.json")
datadir = os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture(scope="module")
def validator(request):
    return val.ExtValidator.with_schema_dir(schemadir)

schemashell = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$extensionSchemas": [ "http://mgi.nist.gov/mgi-json-schema/v0.1" ],
    "id": "urn:goob"
}

def test_NotesType(validator):
    schema = schemashell.copy()
    schema['id'] = "urn:notes"
    schema["type"] = "object"
    schema["properties"] = {
        "sayings": {
            "$ref": "http://mgi.nist.gov/mgi-json-schema/v0.1#/definitions/Notes"
        }
    }
    validator.load_schema(schema)

    inst = {
        "sayings": [ "Hello", "world" ]
    }
    validator.validate_against(inst, [schema['id']])

    inst['sayings'] = "Hello"
    with pytest.raises(val.ValidationError):
        validator.validate_against(inst, [schema['id']])
    
def test_DocumentationType(validator):
    schema = schemashell.copy()
    schema['$ref'] = "http://mgi.nist.gov/mgi-json-schema/v0.1#/definitions/Documentation"
    schema['id'] = "urn:doc"
    validator.load_schema(schema)

    inst = {
        "description": "the def",
        "notes": [ "1", "2" ],
        "comments": [ "yes", "no" ],
        "equivalentTo": "http://schema.org/email"
    }

    validator.validate_against(inst, [schema['id']])

    inst["notes"] = "1, 2"
    with pytest.raises(val.ValidationError):
        validator.validate_against(inst, [schema['id']])
    inst["notes"] = [ "1", "2" ]
    validator.validate_against(inst, [schema['id']])

    inst["comments"] = [ 1, 2 ]
    with pytest.raises(val.ValidationError):
        validator.validate_against(inst, [schema['id']])
    inst["comments"] = [ "yes", "no" ]
    validator.validate_against(inst, [schema['id']])

    inst["description"] = [ "the def" ]
    with pytest.raises(val.ValidationError):
        validator.validate_against(inst, [schema['id']])
    inst["description"] = "the def"
    validator.validate_against(inst, [schema['id']])

    
def test_topdoc():
    schema = schemashell.copy();
    validator = val.ExtValidator.with_schema_dir(schemadir)

    schema['notes'] = [ "yes", "no" ]
    validator.validate(schema, strict=True)
    schema['notes'] = "yes, no" 
    with pytest.raises(val.ValidationError):
        validator.validate(schema, strict=True)
    
def test_definitiondoc():
    schema = schemashell.copy();
    validator = val.ExtValidator.with_schema_dir(schemadir)

    schema['definitions'] = {
        "Name": {
            "type": "string",
            "notes": [ "yes", "no" ]
        }
    }
    validator.validate(schema, strict=True)
    schema['definitions']['Name']['notes'] = "yes, no" 
    with pytest.raises(val.ValidationError):
        validator.validate(schema, strict=True)
    
