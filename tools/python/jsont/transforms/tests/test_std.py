import os, pytest, types

input = { "goob": "gurn" }
context = { "foo": "bar" }
engine = object()

import jsont.transforms.std as std
from xjs.validate import ExtValidator
from jsont.engine import StdEngine
from jsont.exceptions import *

def test_literal():

    t = std.Literal({'value': '{', "$type": "literal"}, engine, "ptr")
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
        config = { "transform": { "$type": "extract", "select": "/contact/name"},
                   "input": { "$type": "json", 
                              "content": { "contact": { "name": "bob" } }} }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({}, {})
        assert out == "bob"

    def test_tname(self, engine):
        config = { "transform": { "$type": "extract", "select": "/contact/name",
                                  "transforms": {
                                     "contactname": {"$type": "json", 
                              "content": { "contact": { "name": "bob" } }} }
                                  },
                   "input": "contactname" }
        #pytest.set_trace()
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({}, {})
        assert out == "bob"

    def test_datapointer(self, engine):
        config = { "transform": { "$type": "extract", "select": "/name" },
                   "input": "/curation/contact" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == "bob"

    def test_datapointer2(self, engine):
        config = { "transform": { "$type": "extract", "select": "/contact/name"},
                   "input": "/curation" }
        transf = std.Apply(config, engine, "goob", "apply")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == "bob"

    def test_function(self, engine):
        config = { "transform": { "$type": "extract", "select": "" },
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

    def test_transform_a(self, engine):
        config = { "select": "/2" }
        transf = std.Extract(config, engine, 'goob', "apply")
        out = transf(["neil", "jack", "me"], {})
        assert out == "me"

    def test_transform_a2(self, engine):
        config = { "select": "" }
        transf = std.Extract(config, engine, 'goob', "apply")
        out = transf(["neil", "jack", "me"], {})
        assert isinstance(out, list)
        assert out[1] == "jack"
        assert len(out) == 3

    def test_function(self, engine):
        config = { "content": "Call {extract(/curation/contact/name)}." }
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf({"curation": { "contact": { "name": "bob" }} }, {})
        assert out == 'Call bob.'

def test_metaprop(engine):
    assert std.metaprop(engine, "gurn", {}, 'goob') == "$goob"
    assert std.metaprop(engine, {"gurn": "goob"}, {}, 'type') == "$type"
    assert std.metaprop(engine, {}, {}, 'val') == "$val"
    assert std.metaprop(engine, {}, {}, 'ins') == "$ins"
    assert std.metaprop(engine, "goob", {}) == "$goob"
    assert std.metaprop(engine, {"gurn": "goob"}, {}) == "${'gurn': 'goob'}"

    transf = engine.resolve_transform("metaprop")
    assert transf("gurn", {}) == "$gurn"

    transf = engine.resolve_transform("metaprop('goob')")
    assert transf("gurn", {}) == "$goob"

    transf = engine.resolve_transform("metaprop(/gurn)")
    assert transf({"gurn": "goob"}, {}) == "$goob"

def test_tostr(engine):
    assert std.tostr(engine, {}, {}, True) == "true"
    assert std.tostr(engine, {}, {}, [ 1, 2, 3 ]) == "[1, 2, 3]"
    assert std.tostr(engine, {}, {}, "glub") == "glub"
    assert std.tostr(engine, True, {}) == "true"
    assert std.tostr(engine, [ 1, 2, 3 ], {}) == "[1, 2, 3]"

    transf = engine.resolve_transform("tostr")
    assert transf(True, {}) == "true"
    assert transf([ 1, 2, 3 ], {}) == "[1, 2, 3]"
    assert transf(False, {}, True) == "true"

    transf = engine.resolve_transform("tostr()")
    assert transf(True, {}) == "true"
    transf = engine.resolve_transform("tostr([ 1, 2, 3 ])")
    assert transf(True, {}) == "[1, 2, 3]"

    # note: can't convert True, False, or None.

def test_wrap(engine):

    text = "convert a paragraph of text into an array of strings broken at word boundarys that are less than a given maximum in length.  "
    split = std.wrap(engine, text, None)
    assert isinstance(split, list)
    assert len(split) == 2
    assert len(split[0]) <= 75
    assert len(split[1]) <= 75
    assert split[0] == "convert a paragraph of text into an array of strings broken at word"
    assert split[1] == "boundarys that are less than a given maximum in length."

    split = std.wrap(engine, text, None, 45)
    assert isinstance(split, list)
    assert len(split) == 3
    assert len(split[0]) <= 45
    assert len(split[1]) <= 45
    assert len(split[2]) <= 45
    assert split[0] == "convert a paragraph of text into an array of"
    assert split[1] == "strings broken at word boundarys that are"
    assert split[2] == "less than a given maximum in length."    

    split = std.wrap(engine, "Yeah, man!", None)
    assert isinstance(split, list)
    assert len(split) == 1
    assert split[0] == "Yeah, man!"

    split = std.wrap(engine, text, None, 40, "Yeah, man!")
    assert isinstance(split, list)
    assert len(split) == 1
    assert split[0] == "Yeah, man!"

    transf = engine.resolve_transform("wrap(75)")
    split = transf(text, None)
    assert isinstance(split, list)
    assert len(split) == 2
    assert len(split[0]) <= 75
    assert len(split[1]) <= 75
    assert split[0] == "convert a paragraph of text into an array of strings broken at word"
    assert split[1] == "boundarys that are less than a given maximum in length."
    
    transf = engine.resolve_transform("wrap(75, 'Yeah, man!')")
    split = transf(text, None)
    assert len(split) == 1
    assert split[0] == "Yeah, man!"

    config = { "$type": "apply",
               "transform": "wrap",
               "args": [ 45 ] }
    transf = engine.make_transform(config)
    split = transf(text, None)
    assert len(split) == 3
    assert len(split[0]) <= 45
    assert len(split[1]) <= 45
    assert len(split[2]) <= 45
    assert split[0] == "convert a paragraph of text into an array of"
    assert split[1] == "strings broken at word boundarys that are"
    assert split[2] == "less than a given maximum in length."    

def test_indent(engine):
    
    out = std.indent(engine, "Yah!", None, 8)
    assert out == "        Yah!"
    out = std.indent(engine, "Yah!", None, 6, "boo!")
    assert out == "      boo!"

    transf = engine.resolve_transform("indent")
    assert transf("goob", {}) == "    goob"
    

class TestMap(object):

    def test_basic(self, engine):
        config = { "itemmap": "indent(4)" }
        transf = std.Map(config, engine, 'goob', "apply")
        out = transf(["neil", "jack", "me"], None)
        assert out == ["    neil", "    jack", "    me"]

    def test_unstrict(self, engine):
        config = { "itemmap": "indent(4)" }
        transf = std.Map(config, engine, 'goob', "apply")
        out = transf("neil", None)
        assert out == ["    neil"]

    def test_strict(self, engine):
        config = { "itemmap": "indent(4)", "strict": True }
        transf = std.Map(config, engine, 'goob', "apply")
        with pytest.raises(TransformInputTypeError):
            out = transf("neil", None)

    def test_function(self, engine):
        config = { "content": "Call {map(indent(4))}." }
        transf = std.StringTemplate(config, engine, "goob", "stringtemplate")
        out = transf(["neil", "jack", "me"], None)
        assert out == 'Call ["    neil", "    jack", "    me"].'


def test_fill(engine):

    text = "convert a paragraph of text into an array of strings broken at word boundarys that are less than a given maximum in length.  "
    config = { "$type": "apply", "transform": "fill" }
    transf = engine.make_transform(config)
    out = transf(text, None)
    assert out == "     convert a paragraph of text into an array of strings broken at word\n     boundarys that are less than a given maximum in length."

    

class TestFunctionTransform(object):

    pass

        


schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))), "schemas", "json")
moddir = os.path.dirname(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename):
    validator.validate_file(os.path.join(schemadir, filename), False, True)

def test_ss(validator):
    ss = os.path.join(moddir, "std_ss.json")
    validate(validator, ss)
