"""
a module providing the transformation engine and utility functions
"""
import os, json, copy

import jsonspec.pointer as jsonptr

from .exceptions import *
from .base import *
from .transforms import std

defaultContext = {
    "$secure": True,
}

class Context(ScopedDict):
    """
    a special dictionary for containing context data.  Keys that begin with
    "$" cannot be overridden.
    """
    CONST_PREFIX = '$'

    def __init__(self, defaults):
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

class DataPointer(object):
    """
    a representation of a data pointer which has two parts:  the intended 
    data target and a "relative" JSON pointer
    """

    @classmethod
    def parse(cls, strrep):
        """
        parse the string representaton of a data pointer into a 2-tuple
        """
        parts = strrep.strip().rsplit(':')
        if len(parts) > 2:
            raise ValueError("Format error (too many ':'): " + strrep)
        if len(parts) == 1:
            if len(parts[0]) == 0:
                raise ValueError("Format error (empty string)")
            parts = [ None, parts[0] ]
        return tuple(parts)

    def __init__(self, strrep=None):
        """
        parse the string representaton of a data pointer
        """
        self.target = None
        self.path = ''
        if strrep:
            (self.target, self.path) = DataPointer.parse(strrep)

    def __str__(self):
        out = ''
        if self.target:
            out += self.target + ':'
        return out + self.path

    def __repr__(self):
        return "DataPointer(target={0}, path={1})".format(repr(self.target),
                                                          repr(self.path))

    def copy(self):
        """
        create a copy of this pointer
        """
        out = DataPointer()
        out.target = self.target
        out.path = self.path
        return out


class Engine(object):
    """
    A class that represents the driver for applying transformations.

    It includes a built in registry of transforms (and templates and joins) 
    and prefix defintions which can be retrieved by name.  The available 
    transforms and prefixes can change depending on the current depth within
    a transform (stylesheet).  To facilitate this, an Engine can wrap another 
    Engine to use the latter's transforms as defaults.  This allows the engine
    to be scoped to a certain layer in the source stylesheets: new transforms
    that are defined in an inner layer will override the outer layer versions
    but will disappear from scope when processing leaves that layer.
    """
    # TODO: context data input

    def __init__(self, currtrans=None, base=None):
        """
        wrap around another engine and then load the transforms and prefixes
        included there.  

        :argument object currtrans: the current transform where sub-transforms
                                    and prefixes may be defined.
        :argument Engin base:  the engine to inherit configuration from
        """
        if currtrans is None:
            currtrans = {}
        self._ct = currtrans

        self._basenjn = base
        if self._basenjn is None:
            self.prefixes = ScopedDict()
            self._transforms = ScopedDict()
            self._templates = set()
            self._joins = set()
            self._transCls = ScopedDict()
        else:
            self.prefixes = ScopedDict(base.prefixes)
            self._transforms = ScopedDict(base._transforms)
            self._templates = set(base._templates)
            self._joins = set(base._joins)
            self._transCls = ScopedDict(base._transCls)


        self.load_transform_defs(currtrans)

        # wrap default transform classes for the different types
        if base:
            self._transCls = ScopedDict(base._transCls)

    def load_transform_defs(self, config):
        """
        load in new transform and prefix definitions from the given 
        configuration.  

        :argument dict config:  the dictionary containing the definitions via
                                its properties, "prefixes", "transforms",
                                "templates", and "joins".
        """
        # load any new prefixes
        self._loadprefixes(config.get('prefixes'))

        # load any new transforms, templates, and joins
        self._loadtransforms(config.get('transforms'))
        self._loadtemplates(config.get('templates'))
        self._loadjoins(config.get('joins'))

    def _loadprefixes(self, defs):
        if not defs:
            return
        if not isinstance(defs, dict):
            raise TransformConfigException("'prefixes' node not a dict: " + 
                                           str(type(defs)))
        self.prefixes.update(defs)

    def _loadtransforms(self, defs):
        if not defs:
            return
        if not isinstance(defs, dict):
            raise TransformConfigException("'transforms' node not a dict: " + 
                                           str(type(defs)))

        for name in defs:
            self.add_transform(name, defs[name])

    def _loadtemplates(self, defs):
        if not defs:
            return
        if not isinstance(defs, dict):
            raise TransformConfigException("'transforms' node not a dict: " + 
                                           str(type(defs)))

        for name in defs:
            self.add_template(name, defs[name])

    def _loadjoins(self, defs):
        if not defs:
            return
        if not isinstance(defs, dict):
            raise TransformConfigException("'transforms' node not a dict: " + 
                                           str(type(defs)))

        for name in defs:
            self.add_join(name, defs[name])

    def add_transform(self, name, config):
        """
        register a named transform.
        """
        self._transforms[name] = config

        if config.get('returns') == 'string':
            self._templates.add(name)
            # TODO: test for joins

    def add_template(self, name, config):
        """
        register a named template.  A Template is a Transform that returns
        a string.
        """
        self._transforms[name] = copy.deepcopy(config)

        if config.get('returns', 'string') != 'string':
            raise TransformConfigParamError('returns', name, 
    name + " template: 'returns' not set to 'string': " + config.get('returns'))
        self._templates.add(name)

    def add_template(self, name, config):
        """
        register a named template.  A Template is a Transform that returns
        a string.
        """
        self.add_transform(name, config)

        if config.get('returns', 'string') != 'string':
            raise TransformConfigParamError('returns', name, 
    name + " template: 'returns' not set to 'string': " + config.get('returns'))
        self._templates.add(name)

    def add_join(self, name, config):
        """
        register a named join.  A Join is a Template that requires the input
        to be an array of strings.
        """
        self.add_template(name, config)
        # test for input type
        self._joins.add(name)

    def resolve_prefix(self, name):
        return self.prefixes.get(name)

    def resolve_transform(self, name):
        """
        resolve the name into a Transform instance, ready for use.  The 
        transform may not have been parsed and constructed into a Transform,
        yet; in this case, this will be done (causing all dependant transforms
        to be parsed as well).

        :exc TransformNotFound: if a transform with that name is not known
        :exc TransformConfigParamError: if the configuration is invalid for 
                                the transform's type.
        """
        try:
            transf = self._transforms[name]
        except KeyError, ex:
            raise TransformNotFound(name)

        if not isinstance(transf, Transform):
            transf = self.make_transform(transf, name)
            self._transforms[name] = transf

        return transf

    def resolve_template(self, name):
        """
        resolve the name into a template Transform instance, ready for use.  
        The template may not have been parsed and constructed into a Transform,
        yet; in this case, this will be done (causing all dependant transforms
        to be parsed as well).

        :exc TransformNotFound: if a transform with that name is not known
        :exc TransformConfigParamError: if the configuration is invalid for 
                                the transform's type.
        """
        if name not in self._templates:
            if name in self._transforms:
                raise TransformNotFound(name, name +
                                      " transform not recognized as a template")
            raise TransformNotFound(name, "template not found: " + name)

        return self.resolve_transform(name)

    def resolve_join(self, name):
        """
        resolve the name into a join Transform instance, ready for use.  The 
        join may not have been parsed and constructed into a Transform,
        yet; in this case, this will be done (causing all dependant transforms
        to be parsed as well.

        :exc TransformNotFound: if a transform with that name is not known
        :exc TransformConfigParamError: if the configuration is invalid for 
                                the transform's type.
        """
        if name not in self._templates:
            if name in self._joins:
                raise TransformNotFound(name, name +
                                        " transform not recognized as a join")
            raise TransformNotFound(name, "join not found: " + name)

        return self.resolve_transform(name)

    def make_transform(self, config, name=None, type=None):
        """
        create a Transform instance from its configuration

        :argument dict config:  the JSON object that defines the transform.  
                                This must have a 'type' property if the type
                                is not given as an argument.
        :argument name str:     the name associated with this template.  If 
                                None, the transform is anonymous.  
        :argument type str:     the type of transform to assume for this 
                                request.  Any 'type' property in the config
                                is ignored.  
        """
        if not type:
            type = config.get('type')
        if not type:
            raise MissingTransformData('type', name)

        try:
            tcls = self._transCls[type]
        except KeyError:
            msg = ""
            if name: msg += name + ": "
            msg += "Unrecognized transform type: " + type
            raise TransformNotFound(name, msg)

        return tcls(config, self, name, type)

    def load_transform_types(self, module):
        """
        load the Transform classes defined in the given module.  The module
        must have a symbol named 'types' that is a dict mapping type names
        to Transform Class objects.  
        """
        if not hasattr(module, 'types'):
            try:
                modname = module.__name__
            except AttributeError, ex:
                raise TransformException("Failed to load tranform types; " +
                                         "not a module? ("+ repr(ex) +")", ex)
            raise TransformException("Failed to load tranform types: missing "+
                                     "'types' dictionary")

        if not isinstance(module.types, dict):
            raise TransformException("Failed to load tranform types: 'types' "+
                                     "is not a dictionary")

        self._transCls.update(module.types)

    def normalize_datapointer(self, dptr, context=None):
        """
        return a new data pointer in which the target prefix has been
        as fully resolve as enabled by the current engine and context

        :argument DataPointer dptr:  the data pointer to normalize, either as
                                     a DataPointer instance or its string 
                                     representation.
        :argument Context context:   the template-specific context to use; if 
                                     None, the engine's default context will 
                                     be used.
        """
        if isinstance(dptr, DataPointer):
            out = dptr.copy()
        else:
            out = DataPointer(dptr)

        if not out.target:
            out.target = "$in"
            return out

        try:
            while out.target != "$in" and out.target != "$context":
                prefix = self.resolve_prefix(out.target)
                if not prefix:
                    break
                (out.target, out.path) = DataPointer.parse(prefix+out.path)
        except ValueError, ex:
            raise StylesheetContentError("Prefix definition for '" + out.target
                                       +"' resulted in invalid data pointer: "
                                       + prefix, ex)
        return out

    def extract(self, input, context, select):
        """
        Use a given data pointer to extract data from either the input data
        or the context.
        """
        use = self.normalize_datapointer(select, context)

        try:
            if use.target == "$in":
                return jsonptr.extract(input, "/"+use.path)
            elif use.target == "$context":
                return jsonptr.extract(context, "/"+use.path)
        except jsonptr.ExtractError, ex:
            raise DataExtractionError.due_to(ex, input, context)
        except Exception, ex:
            raise StylesheetContentError("Data pointer (" + str(self) + 
                                        " does not normalize to useable JSON " +
                                         "pointer: /" + use.path)

        raise StylesheetContentError("Unresolvable prefix: " + use.target)

        return select.extract_from(input, context, self)

class StdEngine(Engine):
    """
    an engine that loads the standard definitions.  
    """

    def __init__(self):
        super(StdEngine, self).__init__()
        self._load_std_defs()

    def _load_std_defs(self):
        # load the std Transform types
        self.load_transform_types(std)

        # load the std transforms and prefixes
        defsfile = os.path.join(os.path.dirname(std.__file__), "std_ss.json")
        with open(defsfile) as fd:
            stddefs = json.load(fd)

        self.load_transform_defs(stddefs)

class DocEngine(Engine):

    def __init__(self, doctrans=None):
        """
        create an Engine from an initial transform.  

        :argument object doctrans: the initial transform sheet
        """
        super(DocEngine, self).__init__(doctrans, StdEngine())
        self.add_transform('', doctrans)

