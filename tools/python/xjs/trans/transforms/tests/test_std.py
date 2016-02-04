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


class TestJSON(object):

    def test_tmpl1(self, engine):
        config = { "content": "{$lb}" }
        transf = std.JSON(config, engine, "goob", "json")
        out = transf({}, {})
        assert out == "{"

    def test_tmpl2(self, engine):
        config = { "content": 4 }
        transf = std.JSON(config, engine, "goob", "json")
        out = transf({}, {})
        assert out == 4

    def test_tmpl3(self, engine):
        config = { "content":  [ True, "[{$lb}{$rb}]", 3]}
        transf = std.JSON(config, engine, "goob", "json")
        out = transf({}, {})
        assert isinstance(out, list)
        assert len(out) == 3
        assert out[0] is True
        assert out[1] == "[{}]"
        assert out[2] is 3

    def test_tmpl4(self, engine):
        config = { "content":  { "a": [True, "[{$lb}{$rb}]", 3],
                                 "b": { "$val": "/numbers" } }    }
        transf = std.JSON(config, engine, "goob", "json")
        out = transf({"numbers": range(3)}, {})
        assert isinstance(out, dict)
        assert len(out) == 2
        assert out['a'][0] is True
        assert out['a'][1] == "[{}]"
        assert out['a'][2] is 3
        assert isinstance(out['b'], list)
        assert out['b'][2] is 2

class TestApply(object):

    def test_anon(self, engine):
        config = { "transform": { "type": "extract", "select": "/contact/name" },
                   "input": { "type": "json", 
                              "content": { "contact": { "name": "bob" } }} }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({}, {})
        assert out == "bob"

    def test_tname(self, engine):
        config = { "transform": { "type": "extract", "select": "/contact/name",
                                  "transforms": {
                                     "contactname": {"type": "json", 
                              "content": { "contact": { "name": "bob" } }} }
                                  },
                   "input": "contactname" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({}, {})
        assert out == "bob"

    def test_datapointer(self, engine):
        config = { "transform": { "type": "extract", "select": "/name" },
                   "input": "/curation/contact" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == "bob"

    def test_datapointer2(self, engine):
        config = { "transform": { "type": "extract", "select": "/contact/name" },
                   "input": "/curation" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == "bob"

    def test_function(self, engine):
        config = { "transform": { "type": "extract", "select": "" },
                   "input": "delimit(' and ')" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf(["neil", "jack", "me"], {})
        assert out == "neil and jack and me"


class TestExtractTransform(object):

    def test_transform(self, engine):
        config = { "select": "/curation/contact/name" }
        transf = std.Extract(config, engine, 'goob', "apply")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == 'bob'

    def test_function(self, engine):
        config = { "content": "Call {extract(/curation/contact/name)}." }
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == 'Call bob.'




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
