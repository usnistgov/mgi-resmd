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

    def test_ins_array(self, engine):
        makearray = { "$type": "json", "content": [ 9, 8, 7 ] }
        config = { "content": { "a": [True, {"$ins": makearray}, 3] }}
        #pytest.set_trace()
        transf = std.JSON(config, engine, "goob", "json")
        out = transf({"numbers": range(3)}, {})
        assert isinstance(out, dict)
        assert isinstance(out['a'], list)
        assert out['a'] == [ True, 9, 8, 7, 3 ]

    def test_ins_object(self, engine):
        makeobj = { "$type": "json", "content": {"foo": "bar", "gurn": "goob"} }
        config = { "content": { "a":    [True, "[{$lb}{$rb}]", 3],
                                "foo": "zub",
                                "$upd": makeobj }}
        #pytest.set_trace()
        transf = std.JSON(config, engine, "goob", "json")
        #pytest.set_trace()
        out = transf({"numbers": range(3)}, {})
        assert isinstance(out, dict)
        assert out['a'] == [ True, "[{}]", 3 ]
        assert "foo" in out
        assert "gurn" in out
        assert out['gurn'] == "goob"
        assert out['foo'] == "bar"

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
        #pytest.set_trace()
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

def test_tobool(engine):
    assert std.tobool(engine, {}, {}, True) is True
    assert std.tobool(engine, {}, {}, False) is False
    assert std.tobool(engine, {}, {}, [ 1, 2, 3 ]) is True
    assert std.tobool(engine, {}, {}, [ ]) is False
    assert std.tobool(engine, {}, {}, "glub") is True
    assert std.tobool(engine, True, {}, "") is False
    assert std.tobool(engine, {"a": 1}, {}) is True
    assert std.tobool(engine, {}, {}) is False
    assert std.tobool(engine, True, {}) is True
    assert std.tobool(engine, [ 1, 2, 3 ], {}) is True

    transf = engine.resolve_transform("tobool")
    assert transf(False, {}) is False
    assert transf([ 1, 2, 3 ], {}) is True
    assert transf(False, {}, True) is True

    transf = engine.resolve_transform("tobool()")
    assert transf(True, {}) is True
    transf = engine.resolve_transform("tobool([ ])")
    assert transf(True, {}) is False

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

def test_isdefined(engine):
    config = { "$type": "apply",
               "transform": "isdefined",
               "args": [ "/a" ] }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)
    assert not transf({ "d": 1, "b": 2 }, None)
    assert not transf([ "d", 1, "b", 2 ], None)
    assert not transf(5, None)
    
def test_istype(engine):
    config = { "$type": "apply",
               "transform": "istype",
               "args": [ "object" ] }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)
    assert not transf([ "d", 1, "b", 2 ], None)
    assert not transf(5, None)
    assert not transf(None, None)
    assert not transf("goob", None)
    assert transf({ "d": 1, "b": 2 }, None)

    config['args'] = [ "object", "/d" ]
    transf = engine.make_transform(config)
    assert not transf({ "d": 1, "b": 2 }, None)

    config['args'] = [ "number", "/a" ]
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)

    config['args'] = [ "integer", "/a" ]
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)

    config['args'] = [ "array" ]
    transf = engine.make_transform(config)
    assert transf([ "d", 1, "b", 2 ], None)
    assert not transf({ "a": 1, "b": 2 }, None)

    config['args'] = [ "string", "/b" ]
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": "h" }, None)

    config['args'] = [ "boolean", "/b" ]
    transf = engine.make_transform(config)
    assert not transf({ "a": 1, "b": "h" }, None)
    assert transf({ "a": 1, "b": False }, None)

    config['args'] = [ "null", "$context:" ]
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)

    config = { "$type": "apply",
               "transform": "istype('number','/b')" }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)

def test_isobject(engine):
    config = { "$type": "apply",
               "transform": "isobject" }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)
    assert not transf(3, None)
    assert not transf(None, None)
    assert not transf("a", None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isobject", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert not transf({ "a": 1, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isobject('$context:')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": 2 })

def test_isarray(engine):
    config = { "$type": "apply",
               "transform": "isarray" }
    transf = engine.make_transform(config)
    assert transf([ "d", 1, "b", 2 ], None)
    assert not transf({ "a": 1, "b": 2 }, None)
    assert not transf(3, None)
    assert not transf(None, None)
    assert not transf("a", None)
    
    config = { "$type": "apply",
               "transform": "isarray", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert not transf({ "a": 1, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isarray('$context:')" }
    transf = engine.make_transform(config)
    assert not transf([ "d", 1, "b", 2 ], None)
    assert transf(None, [ "d", 1, "b", 2 ])

def test_isstring(engine):
    config = { "$type": "apply",
               "transform": "isstring" }
    transf = engine.make_transform(config)
    assert transf("a", None)
    assert not transf({ "a": 1, "b": 2 }, None)
    assert not transf(3, None)
    assert not transf(None, None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isstring", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert transf({ "a": 'b', "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isstring('$context:/b')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": 'g' })

def test_isnumber(engine):
    config = { "$type": "apply",
               "transform": "isnumber" }
    transf = engine.make_transform(config)
    assert transf(3, None)
    assert transf(-3.14159, None)
    assert not transf({ "a": 1, "b": 2.3 }, None)
    assert not transf(None, None)
    assert not transf("a", None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isnumber", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isnumber('$context:/b')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": 2 })
    assert not transf(None, { "a": 1, "b": 'g' })

def test_isinteger(engine):
    config = { "$type": "apply",
               "transform": "isinteger" }
    transf = engine.make_transform(config)
    assert transf(3, None)
    assert not transf(-3.14159, None)
    assert not transf({ "a": 1, "b": 2.3 }, None)
    assert not transf(None, None)
    assert not transf("a", None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isinteger", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert transf({ "a": 1, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isinteger('$context:/b')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": 2 })

def test_isboolean(engine):
    config = { "$type": "apply",
               "transform": "isboolean" }
    transf = engine.make_transform(config)
    assert transf(False, None)
    assert not transf({ "a": 1, "b": 2 }, None)
    assert not transf(3, None)
    assert not transf(None, None)
    assert not transf("a", None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isboolean", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert transf({ "a": True, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isboolean('$context:/b')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": False })

def test_isobject(engine):
    config = { "$type": "apply",
               "transform": "isnull" }
    transf = engine.make_transform(config)
    assert transf(None, None)
    assert not transf({ "a": 1, "b": 2 }, None)
    assert not transf(3, None)
    assert not transf("a", None)
    assert not transf([ "d", 1, "b", 2 ], None)
    
    config = { "$type": "apply",
               "transform": "isnull", "args": ["/a"] }
    transf = engine.make_transform(config)
    assert not transf({ "a": 1, "b": 2 }, None)
    config = { "$type": "apply",
               "transform": "isnull('$context:/b')" }
    transf = engine.make_transform(config)
    assert transf(None, { "a": 1, "b": None })

class  TestChooseTransform(object):

    config = { "$type": "choose",
               "cases": [
                  {
                    "test": "isarray",
                    "transform": "$context:/answers/0"
                  },
                  {
                    "test": "isstring",
                    "transform": "$context:/answers/1"
                  },
                  {
                    "test": "isinteger",
                    "transform": "$context:/answers/2"
                  },
                  {
                    "test": "isobject",
                    "transform": "$context:/answers/3"
                  }
               ],
               "default": "$in:"
             }

    context = {
        "answers": map(lambda c: "choice "+str(c), range(4))
    }

    def test_c0(self, engine):
        transf = engine.make_transform(self.config)
        out = transf([], self.context)
        assert out == "choice 0"

    def test_c1(self, engine):
        transf = engine.make_transform(self.config)
        out = transf("goob", self.context)
        assert out == "choice 1"

    def test_c3(self, engine):
        transf = engine.make_transform(self.config)
        out = transf({}, self.context)
        assert out == "choice 3"

    def test_default(self, engine):
        transf = engine.make_transform(self.config)
        out = transf(4.1, self.context)
        assert out == 4.1
        




    

class TestFunctionTransform(object):

    pass

        


schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))), "schemas", "json")
moddir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "std")

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename):
    validator.validate_file(os.path.join(schemadir, filename), False, True)

def test_ss(validator):
    ss = os.path.join(moddir, "ss.json")
    validate(validator, ss)
