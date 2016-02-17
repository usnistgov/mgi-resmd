"""
a module providing the base utility functions and classes
"""
from collections import MutableMapping
from .exceptions import TransformConfigException, TransformDisabled

class ScopedDict(MutableMapping):

    def __init__(self, defaults=None):
        MutableMapping.__init__(self)
        self._data = {}
        if defaults is None:
            defaults = {}
        self._defaults = defaults

    def __getitem__(self, key):
        try:
            return self._data.__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        return self._defaults[key]

    def __setitem__(self, key, val):
        self._data[key] = val

    def __delitem__(self, key):
        del self._data[key]

    def __keys(self):
        return list(set(self._data.keys()).union(self._defaults))

    def __iter__(self):
        for key in self.__keys():
            yield key

    def __len__(self):
        return len(self.__keys())

    def default_to(self):
        """
        create and return a new dictionary that uses this one as its defaults
        """
        return self.__class__(self)

    @property
    def defaults(self):
        """
        the default dictionary
        """
        return self._defaults

class Context(ScopedDict):
    """
    a special dictionary for containing context data.  Keys that begin with
    "$" cannot be overridden.
    """
    CONST_PREFIX = '$'

    def __init__(self, defaults=None):
        super(Context, self).__init__(defaults)

    def __setitem__(self, key, value):
        if key.startswith(self.CONST_PREFIX):
            raise KeyError(key + ": cannot be updated")
        ScopedDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if key.startswith(self.CONST_PREFIX):
            raise KeyError(key + ": cannot be deleted")
        ScopedDict.__delitem__(self, key)

    def __set(self, key, value):
        try:
            self.__setitem__(key, value)
        except KeyError:
            pass

    def update(self, other=None, **keys):
        if other is not None:
            for key in other:
                self.__set(key, other[key])
        for key in keys:
            self.__set(key, keys[key])

class Transform(object):
    """
    a realization of a tranform that can be applied to input data

    On construction, the implementation will interpret the given configuration 
    data to create a transformation function (the "resolution" stage) which will 
    get applied later to the input document data (the "transformation" stage).
    Subclasses create this function by overriding the mkfn() method; it's output
    is a function that takes an input data object and a context data object 
    and, when called, returns the output of the transform.  

    All transforms accept the common parameters "$type" and "input" as part of 
    their configuration.  The type is used to determine which Transform subclass 
    should be instantiated to provide the tranformation.  Consequently, neither 
    this base Transform class nor the corresponding subclass interpret this 
    value; rather, the Engine class's factory function make_tranform() handles 
    this.  Transform simply stores the type value for passing to any exceptions 
    that might be thrown.

    The "input" parameter allows one to select a subset of the input data to 
    be present to the generated transform function.  The value of the parameter
    can be a named or anonymous transform or a data pointer.  Handling of this 
    parameter, both at resolution time and transformation time, is completely 
    encapsulated in this base Transform class so that the input data presented 
    to the constructed tranform function is the data selected by the input 
    parameter.  If the input parameter is not set, the orgininal input data 
    will be presented unchanged.  
    """

    def __init__(self, config, engine, name=None, type=None, skipwrap=False):
        """
        Construct the transform, storing internally the transformation function
        produced via the mkfn() method.  

        :argument dict config:   the data that configures this Transform
        :argument Engine engine: the Engine object to use to resolve data 
                                   pointers and references to other transforms.
        :argument str name:      the name of this transform (if applicable); 
                                   used for identifying the location of 
                                   exception-raising errors
        :argument str type:      the label used to identify the Transform 
                                   subclass intended to provide the 
                                   transformation.  If not provided, the 
                                   value of the "$type" config parameter; 
                                   otherwise, this label will override.  This
                                   is used for identifying the location of 
                                   exception-raising errors.
        :argument bool skipwrap: Normally (False), if the configuration includes 
                                   new transform definitions or prefixes, this 
                                   constructor will create a new Engine (wrapping
                                   the given one) with the new defintions loaded
                                   in.  If True, this wrapping will be skipped
                                   regardless. 
        """
        self.name = name
        if not type:
            type = config.get('$type')
        self.type = type
        self.config = config

        self.engine = self._engine_to_use(engine, skipwrap)
        self._check_status(config, engine)
        self._func = self.mkfn(config, engine)

    def _engine_to_use(self, engine, skipwrap):
        if skipwrap: 
            return engine

        # wrap the engine if necessary
        for prop in "prefixes transforms context".split():
            if prop in self.config:
                # the context is updated for this transform; update it via a 
                # new engine
                return engine.wrap(self.config)
        return engine

    def __call__(self, input, context, *args):
        return self._func(input, context, *args)

    def _check_status(self, config, engine):
        if config.get("status") == "disabled":
            raise TransformDisabled(self.name)

    def _mkfn(self, config, engine):
        # this method returns a wrapper around the transformation function
        # provided by the subclass (mkfn()) that will handle the subselection 
        # of the input 

        input_transf = None
        if "input" in config:
            input_transf = self._resolve_input(config['input'], engine)

        transf = self.mkfn(config, engine)

        def _impl(input, context, *args):
            if input_transf:
                input = input_transf(input, context)
            return transf(input, context)

        return _impl

    def mkfn(self, config, engine):
        def impl(input, context, *args):
            return input
        return impl

    def _resolve_input(self, input, engine):

        if isinstance(input, dict):
            if "$type" in input:
                # this is an anonymous transform configuration object
                return engine.make_transform(input, "(anon)")

            elif "$val" in input:
                return self._resolve_input(input['$val'], engine)

            # else assume it's a JSON transform
            return engine.make_JSON_tranform(input)

        if input is None:
            # user wants the original input unchanged
            return None

        if not isinstance(input, str) and not isinstance(input, unicode):
            raise TransformConfigTypeError('input', 'dict or str', type(input))

        if input.strip() == '':
            # user wants the original input unchanged
            return None

        if '(' in input or ')' in input:
            return engine.resolve_transform(input)

        if ':' in input or input.startswith('/'):
            # it's a pointer
            return Extract({ "select": input }, engine, 
                           (self.name or "extract")+":(select)", "extract")

        # see if it matches a transform or transform-function
        # (may raise a TransformNotFound)
        return engine.resolve_transform(input)

