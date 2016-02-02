import os, pytest, types

input = { "goob": "gurn" }
context = { "foo": "bar" }
engine = object()

import xjs.trans.transforms.std as std
from xjs.validate import ExtValidator
from xjs.trans.engine import StdEngine

def test_literal():

    t = std.Literal({'value': '{', "type": "literal"}, engine, "ptr")
    assert t(input, context) == '{'

@pytest.fixture(scope="module")
def engine(request):
    return StdEngine()

class TestStringTemplate(object):

    def test_tmpl1(self, engine):
        config = {"content": "displaying braces: {$lb}{$rb}"}
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf({}, {})
        assert out == "displaying braces: {}"

    def test_tmpl2(self, engine):
        config = {"content": "{$lb}"}
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf({}, {})
        assert out == "{"

    def test_tmpl2(self, engine):
        config = {"content": "{$lb"}
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf({}, {})
        assert out == "{$lb"

    def test_tmpl3(self, engine):
        config = {"content": "{delimit(' and ')}" }
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf(["neil", "jack", "me"], {})
        assert out == "neil and jack and me"



class TestFunctionTransform(object):

    pass

        


schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))), "schemas", "json")
moddir = os.path.dirname(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename):
    validator.validate_file(os.path.join(schemadir, filename), False, True)

def test_ss(validator):
    ss = os.path.join(moddir, "std_ss.json")
    validate(validator, ss)
