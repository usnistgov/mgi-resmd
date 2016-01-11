import os, pytest, types

input = { "goob": "gurn" }
context = { "foo": "bar" }
engine = object()

import xjs.trans.transforms.std as std

def test_literal():
    f = std.literal(engine, {'value': '{', "type": "literal"})
    assert isinstance(f, types.FunctionType)
    assert f(engine, input, context) == '{'

    f = std.literal(engine, {'value': '}', "type": "literal"})
    assert isinstance(f, types.FunctionType)
    assert f(engine, input, context) == '}'


