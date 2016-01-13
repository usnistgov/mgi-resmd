"""
a module providing the transformation engine and utility functions
"""
import os, json

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
        self.translu[""] = self._stylesheet
        if self._stylesheet.get("returns") == "string":
            self._templates[""] = self._stylesheet

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
        self.transtypes.update(std.types)

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

    def resolve_prefix(self, prefix):
        """
        return the expanded data-pointer value for a prefix
        """
        return self.prefixes.get(prefix)

    def resolve_template(self, name, *args):
        config = self.find_template_config(name)
        if config is None:
            raise TransformNotFound(name)

        return self.make_transform(config, name)

    def resolve_transform(self, name, *args):
        """
        return the tranform function
        """
        config = self.find_transform_config(name)
        if config is None:
            raise TransformNotFound(name)

        return self.make_transform(config, name)

    def make_transform(self, config, name=None, type=None):
        if not type:
            type = config.get('type', '')
        try:
            tcls = self.transtypes[type]
        except KeyError:
            msg = ""
            if name: msg += name + ": "
            msg += "Unrecognized transform type: " + type
            raise TransformNotFound(name, msg)

        return tcls(config, self, name, type)


    
