import os, pytest, json

input = { "goob": "gurn" }
context = { "foo": "bar", "$count": 4 }

import jsont.base as base

class TestScopedDict(object):

    def test_def(self):
        ctx = base.ScopedDict(context)
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

        ctx['$count'] = 5

    def test_keys(self):
        ctx = base.ScopedDict(context)
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
        ctx = base.ScopedDict(context)
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

    def test_nodefs(self):
        ctx = base.ScopedDict()
        assert ctx._defaults is not None
        assert 'foo' not in ctx.keys()
        assert 'foo' not in ctx
        assert len(ctx) == 0
        assert ctx.get('foo') is None

        ctx['foo'] = 'blah'
        assert ctx.get('foo') == 'blah'
        assert 'foo' in ctx
        assert len(ctx) == 1


class TestTransform(object):

    engine = "engine"

    def test_ctor(self):
        trfm = base.Transform({'$type': 'fake'}, self.engine)
        assert trfm.name is None
        assert trfm.type == 'fake'
        assert trfm.config['$type'] == 'fake'
        assert trfm.engine is self.engine
        assert trfm._func is not None

        trfm = base.Transform({'$type': 'fake'}, self.engine, "identity")
        assert trfm.name == "identity"
        assert trfm.type == 'fake'
        assert trfm.config['$type'] == 'fake'
        assert trfm.engine is self.engine
        assert trfm._func is not None

        trfm = base.Transform({'$type': 'fake'}, self.engine, "identity", "goob")
        assert trfm.name == "identity"
        assert trfm.type == 'goob'
        assert trfm.config['$type'] == 'fake'
        assert trfm.engine is self.engine
        assert trfm._func is not None

    def test_disabled(self):
        with pytest.raises(base.TransformConfigException):
            trfm = base.Transform({'$type': 'fake', 'status': 'disabled'}, 
                                  self.engine)

        trfm = base.Transform({'$type': 'fake', 'status': 'enabled'}, 
                              self.engine)
        assert trfm.name is None
        assert trfm.type == 'fake'
        assert trfm.config['$type'] == 'fake'
        assert trfm.engine is self.engine
        assert trfm._func is not None

    def test_callable(self):
        trfm = base.Transform({'$type': 'fake'}, self.engine, "identity")
        assert trfm("value", {}) == "value"



