"""
a module providing the transformation engine and utility functions
"""
import os, json
from collections import MutableMapping

from .exceptions import *
from .transforms import std

defaultContext = {
    "$secure": True,
}

class ScopedDict(MutableMapping):

    def __init__(self, defaults=None):
        MutableMapping.__init__(self)
        self._data = {}
        if defaults is None:
            defaults == {}
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
        return (parts)

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

    def copy(self):
        out = DataPointer()
        out.target = self.target
        out.path = self.path
        return out

    def normalize(self, engine):
        if not self.target:
            self.target = "$in"
            return

        out = self.copy()
        try:
            while out.target != "$in" and out.target != "$context":
                prefix = engine.resolve_prefix(out.target)
                if not prefix:
                    break
                out = DataPointer.parse(prefix+out.path)
        except ValueError, ex:
            raise StylesheetContentError("Prefix definition for '" + out.target
                                       +"' resulting in invalid data pointer: "
                                       + prefix, ex)
        return out

    def extract_from(input, context, engine):
        use = self.normalize(engine)

        try:
            if use.target == "$in":
                return jsonspec.extract(input, "/"+use.path)
            elif use.target == "$context":
                return jsonspec.extract(context, "/"+use.path)
        except Exception, ex:
            raise StylesheetContentError("Data pointer (" + str(self) + 
                                         "does not normalize to useable JSON " +
                                         "pointer: /" + use.path)

        raise StylesheetContentError("Unresolvable prefix: " + use.target)


class Engine(object):

    def __init__(self, stylesheet=None, context=None):
        self._context = ScopedDict(defaultContext)
        if context:
            self._context.update(context)

        if not stylesheet:
            stylesheet = {}
        self._stylesheet = stylesheet

        self.prefixes = dict(self._stylesheet.get("prefixes", {}))

        self.translu = None
        self._templates = None
        self._load_transforms()
        rt = self._stylesheet.get("roottemplate")
        if rt:
            self.translu["roottemplate"] = rt
            self._templates["roottemplate"] = rt

        self.transtypes = None
        self._load_transform_types()

    def _load_transforms(self):
        systrans = os.path.join(os.path.dirname(__file__), "transforms", 
                                "std_ss.json")
        with open(systrans) as fd:
            systrans = json.load(fd)
        self._load_transforms_from(systrans)
        self._load_transforms_from(self._stylesheet)

    def _load_transforms_from(self, sheet):
        if self.translu is None:
            self.translu = ScopedDict(sheet.get('transforms', {}))
        else:
            self.translu.update(sheet.get('transforms', {}))
        self.translu = self.translu.default_to()
        if self._templates is None:
            self._templates = ScopedDict(sheet.get('templates', {}))
        else:
            self._templates.update(sheet.get('templates', {}))
        self._templates = self._templates.default_to()

        for type in "templates joins".split():
            lu = sheet.get(type)
            if lu:
                self.translu.update(lu)
                self.translu = self.translu.default_to()


    def _load_transform_types(self):
        if self.transtypes is None:
            self.transtypes = {}
        for type in std.types:
            self.transtypes[type] = getattr(std, type)

    @property
    def stylesheet(self):
        return ScopedDict(self._stylesheet)

    @property
    def templates(self):
        return ScopedDict(self._templates)

    @property
    def transforms(self):
        return ScopedDict(self._stylesheet.get('transforms'))

    def find_transform_config(self, name):
        """
        find the transform configuration with the given name
        """
        return self.translu.get(name)

    def find_template_config(self, name):
        """
        find the template configuration with the given name
        """
        return self._templates.get(name)

    def extract(self, input, context, select):
        """
        Use a given data pointer to extract data from either the input data
        or the context.
        """
        select = DataPointer(select).normalize(self)
        return select.extract_from(input, context, self)

    def resolve_prefix(self, prefix):
        """
        return the expanded data-pointer value for a prefix
        """
        return self.prefixes.get(prefix)

    def resolve_template(self, name, *args):
        config = self.find_template_config(name)
        if config is None:
            raise TransformNotFound(name)

        typefunc = self.function_for_type(config['type'])
        if typefunc is None:
            raise TransformConfigError("type", name, 
                                       "unknown template type: " + config.type)
        return typefunc(self, config)


    def resolve_transform(self, name, *args):
        """
        return the tranform function
        """
        config = self.find_transform_config(name)
        if config is None:
            raise TransformNotFound(name)

        typefunc = self.function_for_type(config['type'])
        if typefunc is None:
            raise TransformConfigError("type", name, 
                                       "unknown transform type: " + config.type)
        return typefunc(self, config)
        

    def function_for_type(self, type):
        return self.transtypes.get(type)


    
