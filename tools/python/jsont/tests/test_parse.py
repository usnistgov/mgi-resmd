import os, pytest

import jsont.parse as parse

def test_chomp_quote():
    quote, rest = parse.chomp_quote("'goob'--")
    assert quote == "'goob'"
    assert rest == "--"

    quote, rest = parse.chomp_quote('"goob"er')
    assert quote == '"goob"'
    assert rest == "er"

    quote, rest = parse.chomp_quote("'goob'")
    assert quote == "'goob'"
    assert rest == ""

    quote, rest = parse.chomp_quote('"goob"')
    assert quote == '"goob"'
    assert rest == ""

    quote, rest = parse.chomp_quote('""":')
    assert quote == '""'
    assert rest == '":'

    quote, rest = parse.chomp_quote('"\\"":')
    assert quote == '"\\""'
    assert rest == ':'
    quote, rest = parse.chomp_quote('"\\\\"":')
    assert quote == '"\\\\"'
    assert rest == '":'

    with pytest.raises(parse.ConfigSyntaxError):
        quite, rest = parse.chomp_quote('"asdg alsdkf ')

def test_chomp_br():
    encl, rest = parse.chomp_br_enclosure('{asdfk},')
    assert encl == '{asdfk}'
    assert rest == ','

    encl, rest = parse.chomp_br_enclosure('{asdfk}')
    assert encl == '{asdfk}'
    assert rest == ''

    encl, rest = parse.chomp_br_enclosure('{as"1{1"dfk},')
    assert encl == '{as"1{1"dfk}'
    assert rest == ','
    encl, rest = parse.chomp_br_enclosure("{as'1{1'dfk},")
    assert encl == "{as'1{1'dfk}"
    assert rest == ','

    encl, rest = parse.chomp_br_enclosure('{a{{s[d}}fk} asdkf')
    assert encl == '{a{{s[d}}fk}'
    assert rest == ' asdkf'

    with pytest.raises(parse.ConfigSyntaxError):
        encl, rest = parse.chomp_br_enclosure('{a{{s[d}fk} asdkf')

    encl, rest = parse.chomp_br_enclosure('[asdfk],')
    assert encl == '[asdfk]'
    assert rest == ','

    encl, rest = parse.chomp_br_enclosure('[asdfk]')
    assert encl == '[asdfk]'
    assert rest == ''

    encl, rest = parse.chomp_br_enclosure('[as"1[1"dfk],')
    assert encl == '[as"1[1"dfk]'
    assert rest == ','
    encl, rest = parse.chomp_br_enclosure("[as'1[,1' dfk],")
    assert encl == "[as'1[,1' dfk]"
    assert rest == ','

    encl, rest = parse.chomp_br_enclosure('[a[[s, {d]]fk] asdkf')
    assert encl == '[a[[s, {d]]fk]'
    assert rest == ' asdkf'

    with pytest.raises(parse.ConfigSyntaxError):
        encl, rest = parse.chomp_br_enclosure('[a[[s{d]fk] asdkf')

def test_chomp_arg():
    encl, rest = parse.chomp_arg('gab/goob, gurn')
    assert encl == 'gab/goob'
    assert rest == 'gurn'

    encl, rest = parse.chomp_arg('g[ab/goob, g]urn')
    assert encl == 'g[ab/goob'
    assert rest == 'g]urn'

    encl, rest = parse.chomp_arg('{"gab": "goob", "foo": "bar"}, gurn')
    assert encl == '{"gab": "goob", "foo": "bar"}'
    assert rest == 'gurn'

    encl, rest = parse.chomp_arg('"gab[\'goob\']" , gurn')
    assert encl == '"gab[\'goob\']"'
    assert rest == 'gurn'

    encl, rest = parse.chomp_arg("'gab[\"goob\"]' , gurn")
    assert encl == "'gab[\"goob\"]'"
    assert rest == 'gurn'

    encl, rest = parse.chomp_arg('["gab", 3, true, "foo"], gurn')
    assert encl == '["gab", 3, true, "foo"]'
    assert rest == 'gurn'


def test_parse_argstr():
    args = parse.parse_argstr('foo/bar, {"goob": "gurn", "a": 3}, [true, false], "$lb{auths]$rb"')
    assert args[0] == 'foo/bar'
    assert args[1] == '{"goob": "gurn", "a": 3}'
    assert args[2] == '[true, false]'
    assert args[3] == '"$lb{auths]$rb"'
    assert len(args) == 4

def test_parse_function():
    name, args = parse.parse_function('apply(\'goob,1\', true, {"goob": "h["}, [1, 2])')
    assert name == "apply"
    assert args[0] == "'goob,1'"
    assert args[1] == "true"
    assert args[2] == '{"goob": "h["}'
    assert args[3] == '[1, 2]'
    assert len(args) == 4

def test_parse_function_err():
    with pytest.raises(parse.FunctionSyntaxError):
        name, args = parse.parse_function('apply(\'goob,1\', true')

    with pytest.raises(parse.FunctionSyntaxError):
        name, args = parse.parse_function('(\'goob,1\', true)')

    with pytest.raises(parse.FunctionSyntaxError):
        name, args = parse.parse_function('apply \'goob,1\', true)')

    with pytest.raises(parse.FunctionSyntaxError):
        name, args = parse.parse_function('apply("goob,1\', true')


