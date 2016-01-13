import os, pytest, types

input = { "goob": "gurn" }
context = { "foo": "bar" }
engine = object()

import xjs.trans.transforms.std as std

def test_literal():

    t = std.Literal({'value': '{', "type": "literal"}, engine, "ptr")
    assert t(input, context) == '{'


