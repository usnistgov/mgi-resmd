import os, pytest, types

input = { "goob": "gurn" }
context = { "foo": "bar" }
engine = object()

import xjs.trans.transforms.std as std
from xjs.validate import ExtValidator

def test_literal():

    t = std.Literal({'value': '{', "type": "literal"}, engine, "ptr")
    assert t(input, context) == '{'

class TestFunctionTransform(object):

    def test_chomp_quote(self):
        quote, rest = std.Function._chomp_quote("'goob'--")
        assert quote == "'goob'"
        assert rest == "--"

        quote, rest = std.Function._chomp_quote('"goob"er')
        assert quote == '"goob"'
        assert rest == "er"

        quote, rest = std.Function._chomp_quote("'goob'")
        assert quote == "'goob'"
        assert rest == ""

        quote, rest = std.Function._chomp_quote('"goob"')
        assert quote == '"goob"'
        assert rest == ""

        quote, rest = std.Function._chomp_quote('""":')
        assert quote == '""'
        assert rest == '":'

        quote, rest = std.Function._chomp_quote('"\\"":')
        assert quote == '"\\""'
        assert rest == ':'
        quote, rest = std.Function._chomp_quote('"\\\\"":')
        assert quote == '"\\\\"'
        assert rest == '":'

        with pytest.raises(std.FunctionSyntaxError):
            quite, rest = std.Function._chomp_quote('"asdg alsdkf ')

    def test_chomp_br(self):
        encl, rest = std.Function._chomp_br_enclosure('{asdfk},')
        assert encl == '{asdfk}'
        assert rest == ','

        encl, rest = std.Function._chomp_br_enclosure('{asdfk}')
        assert encl == '{asdfk}'
        assert rest == ''

        encl, rest = std.Function._chomp_br_enclosure('{as"1{1"dfk},')
        assert encl == '{as"1{1"dfk}'
        assert rest == ','
        encl, rest = std.Function._chomp_br_enclosure("{as'1{1'dfk},")
        assert encl == "{as'1{1'dfk}"
        assert rest == ','

        encl, rest = std.Function._chomp_br_enclosure('{a{{s[d}}fk} asdkf')
        assert encl == '{a{{s[d}}fk}'
        assert rest == 'asdkf'

        with pytest.raises(std.FunctionSyntaxError):
            encl, rest = std.Function._chomp_br_enclosure('{a{{s[d}fk} asdkf')

        encl, rest = std.Function._chomp_br_enclosure('[asdfk],')
        assert encl == '[asdfk]'
        assert rest == ','

        encl, rest = std.Function._chomp_br_enclosure('[asdfk]')
        assert encl == '[asdfk]'
        assert rest == ''

        encl, rest = std.Function._chomp_br_enclosure('[as"1[1"dfk],')
        assert encl == '[as"1[1"dfk]'
        assert rest == ','
        encl, rest = std.Function._chomp_br_enclosure("[as'1[,1' dfk],")
        assert encl == "[as'1[,1' dfk]"
        assert rest == ','

        encl, rest = std.Function._chomp_br_enclosure('[a[[s, {d]]fk] asdkf')
        assert encl == '[a[[s, {d]]fk]'
        assert rest == 'asdkf'

        with pytest.raises(std.FunctionSyntaxError):
            encl, rest = std.Function._chomp_br_enclosure('[a[[s{d]fk] asdkf')

    def test_chomp_arg(self):
        encl, rest = std.Function._chomp_arg('gab/goob, gurn')
        assert encl == 'gab/goob'
        assert rest == 'gurn'

        encl, rest = std.Function._chomp_arg('g[ab/goob, g]urn')
        assert encl == 'g[ab/goob'
        assert rest == 'g]urn'

        encl, rest = std.Function._chomp_arg('{"gab": "goob", "foo": "bar"}, gurn')
        assert encl == '{"gab": "goob", "foo": "bar"}'
        assert rest == 'gurn'

        encl, rest = std.Function._chomp_arg('"gab[\'goob\']" , gurn')
        assert encl == '"gab[\'goob\']"'
        assert rest == 'gurn'

        encl, rest = std.Function._chomp_arg("'gab[\"goob\"]' , gurn")
        assert encl == "'gab[\"goob\"]'"
        assert rest == 'gurn'

        encl, rest = std.Function._chomp_arg('["gab", 3, true, "foo"], gurn')
        assert encl == '["gab", 3, true, "foo"]'
        assert rest == 'gurn'

    def test_parse_argstr(self):
        args = std.Function._parse_argstr('foo/bar, {"goob": "gurn", "a": 3}, [true, false], "$lb{auths]$rb"')
        assert args[0] == 'foo/bar'
        assert args[1] == '{"goob": "gurn", "a": 3}'
        assert args[2] == '[true, false]'
        assert args[3] == '"$lb{auths]$rb"'



        


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
