import os, pytest, json

input = { "goob": "gurn" }
context = { "foo": "bar", "$count": 4 }

import xjs.trans.engine as njn

class TestContext(object):

    def test_def(self):
        ctx = njn.Context(context)
        assert ctx.defaults is context
        assert ctx['foo'] == 'bar'
        with pytest.raises(KeyError):
            ctx['hank']

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        assert ctx['hank'] == 3
        assert ctx['foo'] == 'blah'

        del ctx['hank'] 
        del ctx['foo'] 
        assert ctx['foo'] == 'bar'
        with pytest.raises(KeyError):
            ctx['hank']

    def test_keys(self):
        ctx = njn.Context(context)
        assert ctx.defaults is context
        keys = ctx.keys()
        assert 'foo' in keys
        assert 'hank' not in keys
        assert len(keys) == 2

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        keys = ctx.keys()
        assert 'foo' in keys
        assert 'hank' in keys
        assert len(keys) == 3

    def test_iter(self):
        ctx = njn.Context(context)
        assert ctx.defaults is context
        # pytest.set_trace()
        assert 'foo' in set(ctx.iterkeys())
        assert 'foo' in ctx
        assert 'hank' not in ctx
        assert len(ctx) == 2

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        assert 'foo' in ctx
        assert 'hank' in ctx
        assert len(ctx) == 3

    def test_protected(self):
        ctx = njn.Context(context)

        with pytest.raises(KeyError):
            ctx['$count'] = 5

        with pytest.raises(KeyError):
            ctx['$secure'] = False

        ctx.update({"dr": "eamon", "$count": 5, "$secure": False})
        assert ctx["dr"] == "eamon"
        assert ctx["$count"] == 4
        assert "$secure" not in ctx

        with pytest.raises(KeyError):
            del ctx['$count']

class TestDataPointer(object):

    pass

exdir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))), "examples",
                     "jstrans")

class TestExamples(object):

    def test_simple(self):
        ss = { "type": "literal", "value": "@" }
        engine = njn.StdEngine()
        tfunc = engine.make_transform(ss, "$at")
        result = tfunc({}, {})
        assert result == "@"

    def test_template1(self):

        with open(os.path.join(exdir,"testtemplate1.json")) as fd:
            ss = json.load(fd)

        engine = njn.DocEngine(ss)

        tfunc = engine.resolve_template('')
        result = tfunc({}, {})
        
        assert result == "a substitution token looks like this: {texpr}"

    def test_template2(self):
        input = { "contact": { "name": "Bob", "email": "bob@gmail.com" }}

        with open(os.path.join(exdir,"testtemplate2.json")) as fd:
            ss = json.load(fd)

        engine = njn.DocEngine(ss)

        tfunc = engine.resolve_template('')
        result = tfunc(input, {})
        
        assert result == "Contact Bob via <bob@gmail.com>"

