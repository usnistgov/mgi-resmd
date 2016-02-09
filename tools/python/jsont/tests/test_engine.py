import os, pytest, json
from cStringIO import StringIO

input = { "goob": "gurn" }
context = { "foo": "bar", "$count": 4 }

import jsont.engine as njn

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

    #TODO
    pass

class TestStdEngine(object):

    def test_loading(self):
        engine = njn.StdEngine()

        assert "literal" in engine._transCls
        assert "$lb" in engine._transforms

    def test_transform_lb(self):
        engine = njn.StdEngine()
        t = engine.resolve_transform("$lb")
        assert isinstance(t, njn.Transform)
        assert t(engine, {}, {}) == '{'

    def test_validate(self):
        engine = njn.StdEngine()
        engine.resolve_all_transforms()

        assert "$lb" in engine._transforms
        assert isinstance(engine._transforms["$lb"], njn.Transform)
        

exdir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))), "examples",
                     "jsont")

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
        result = engine.transform({})
        
        assert result == "a substitution token looks like this: {texpr}"

        ostrm = StringIO()
        engine.write(ostrm, {})
        assert result+'\n' == ostrm.getvalue()

        ostrm = StringIO()
        engine.write(ostrm, {}, True)
        assert '"'+result+'"\n' == ostrm.getvalue()

    def test_template2(self):
        input = { "contact": { "name": "Bob", "email": "bob@gmail.com" }}

        with open(os.path.join(exdir,"testtemplate2.json")) as fd:
            ss = json.load(fd)

        engine = njn.DocEngine(ss)
        result = engine.transform(input)
        
        assert result == "Contact Bob via <bob@gmail.com>"

    def test_template3(self):
        input = { "contact": { "name": "Bob", "email": "bob@gmail.com" }}

        with open(os.path.join(exdir,"testtemplate3.json")) as fd:
            ss = json.load(fd)

        engine = njn.DocEngine(ss)
        result = engine.transform(input)
        
        assert result == "Contact Bob via <bob@gmail.com>"

    def test_template4(self):
        input = { "contact": { "name": "Bob", "email": "bob@gmail.com" }}

        with open(os.path.join(exdir,"testtemplate4.json")) as fd:
            ss = json.load(fd)

        engine = njn.DocEngine(ss)
        result = engine.transform(input)
        
        assert isinstance(result, dict)
        assert result['contacts'][0].keys()[0] == "Bob"
        assert result['contacts'][0]["Bob"] == "Bob <bob@gmail.com>"

        


