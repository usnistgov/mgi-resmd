"""
a module providing the transformation engine and utility functions
"""
import os, json, copy

import jsonspec.pointer as jsonptr

from .exceptions import *
from .base import *
from .transforms import std, xml
from . import parse

defaultContext = {
    "$secure": True,
}

class DataPointer(object):
    """
    a representation of a data pointer which has two parts:  the intended 
    data target and a "relative" JSON pointer
    """

    @classmethod
    def parse(cls, strrep):
        """
        parse the string representaton of a data pointer into a 2-tuple

        data_pointer := target ':' json_pointer
        target := prefix | resolved_target
        resolved_target := '$' ( 'in' | 'context' )
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

    It includes a built-in registry of transforms 
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
        :argument Engine base:  the engine to inherit configuration from
        """
        if currtrans is None:
            currtrans = {}
        self._ct = None
        self._cfg = None
        if isinstance(currtrans, Transform):
            self._ct = currtrans
        else:
            self._cfg = currtrans

        self._basenjn = base
        if self._basenjn is None:
            self.prefixes = ScopedDict()
            self._transforms = ScopedDict()
            self._transCls = ScopedDict()
            self.context = Context()
            self._system = ScopedDict(DEFAULT_ENV)
        else:
            self.prefixes = ScopedDict(base.prefixes)
            self._transforms = ScopedDict(base._transforms)
            self._transCls = ScopedDict(base._transCls)
            self.context = Context(base.context)

            self._system = base._system

        self.load_transform_defs(currtrans)
        self.update_context(currtrans)

        # wrap default transform classes for the different types
        if base:
            self._transCls = ScopedDict(base._transCls)

    def update_context(self, trans):
        """
        update the context data from the new definitions in the given
        transform configuration
        """
        if trans.has_key('context') and isinstance(trans['context'], dict):
            self.context.update(trans['context'])

    def load_transform_defs(self, config):
        """
        load in new transform and prefix definitions from the given 
        configuration.  

        :argument dict config:  the dictionary containing the definitions via
                                its properties, "prefixes" and "transforms"
        """
        # load any new prefixes
        self._loadprefixes(config.get('prefixes'))

        # load any new transforms
        self._loadtransforms(config.get('transforms'))

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

    def add_transform(self, name, config):
        """
        register a named transform.
        """
        self._transforms[name] = config

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
        # first see if the tranform invocation (i.e. the name) matches the 
        # functional form
        if std.Function.matches(name):
            return std.Function.parse(self, name)
        if '(' in name or ')' in name:
            raise parse.ConfigSyntaxError("Syntax error while invoking function (?): " + name)

        try:
            transf = self._transforms[name]
        except KeyError, ex:
            raise TransformNotFound(name)

        if not isinstance(transf, Transform):
            # determine if we need to update the context with a new engine
            transf = self.make_transform(transf, name)
            self._transforms[name] = transf

        return transf

    def make_transform(self, config, name=None, type=None, ignorecontext=False):
        """
        create a Transform instance from its configuration

        :argument dict config:  the JSON object that defines the transform.  
                                This must have a '$type' property if the type
                                is not given as an argument.
        :argument name str:     the name associated with this transform.  If 
                                None, the transform is anonymous.  
        :argument type str:     the type of transform to assume for this 
                                request.  Any '$type' property in the config
                                is ignored.  
        :argument ignorecontext boolean:  ignore any changes to the context 
                                (i.e. new transforms, prefixes, and context 
                                data) included in the transform configuration.
        """
        if not type:
            type = config.get('$type')
        if not type:
            return Transform(config, self, name, type="identity")

        try:
            tcls = self._transCls[type]
        except KeyError:
            if config.get('status') == 'disabled':
                raise TransformDisabled(name)

            msg = ""
            if name: msg += name + ": "
            msg += "Unrecognized transform type: " + type
            raise TransformNotFound(name, msg)

        return tcls(config, self, name, type, ignorecontext)

    def make_JSON_transform(self, template, input=None):
        """
        convert the given JSON data template into a JSON Transform instance.
        A JSON data template is a JSON structure (dict, list, or string) that
        contains embedded substitution directives.  Such a directive comes in 
        one of four forms:
           * a sub string within a string value of the form {...}, where the
             the contents inside the braces is a transform name or a data 
             pointer.  This braces and its contents will be replaced with a 
             string value resulting from the application of the transform or 
             pointer to the input data.  This can appear in either property
             names or in string values.
           * an object (dict) containing a "$val" property.  The value of this
             property can be an anonymous or named transform or data poitner. 
             This object containg "$val" will be replaced by the result of 
             applying the transform/pointer to the input data.
           * an array (list) item that is an object containing a "$ins" property.
             The value of this property is interpreted in the same way as "$val"
             except that the result of applying the transform is expected to be
             an array (list).  The object containing the "$ins" property will be
             replaced by the items from the transform result and, thus, inserted
             into the containing array. 
           * an object (dict) containing a "$type" property.  The value of this
             string is a string.  This object will be interpreted as an 
             anonymous transform and will be replaced by the result of applying 
             it to the input data
           
        :argument template: the JSON structure containing {} directives
        :argument input:  a reference to a transform to apply to select data
                          from the input data to apply to the template.  
        :returns JSON: a JSON Tranform instance
        """
        return std.JSON({"content": template, "input": input},
                        name="(anon)", type="json")

    def resolve_all_transforms(self):
        """
        ensure that all loaded transform configurations have been resolved
        into Transform instances.  This effectively validates the transform
        configurations.  This will skip over any disabled transforms.
        """
        for name in self._transforms:
            try:
                self.resolve_transform(name)
            except TransformDisabled:
                continue

    def normalize_datapointer(self, dptr, context=None):
        """
        return a new data pointer in which the target prefix has been
        as fully resolve as enabled by the current engine and context

        :argument DataPointer dptr:  the data pointer to normalize, either as
                                     a DataPointer instance or its string 
                                     representation.
        :argument Context context:   the transform-specific context to use; if 
                                     None, the engine's default context will 
                                     be used.
        """
        resolved_targets = ("$in", "$context")

        if isinstance(dptr, DataPointer):
            out = dptr.copy()
        else:
            out = DataPointer(dptr)

        if not out.target:
            out.target = "$in"
            return out

        try:
            while out.target not in resolved_targets:
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
                return jsonptr.extract(input, use.path)
            elif use.target == "$context":
                return jsonptr.extract(context, use.path)
        except jsonptr.ExtractError, ex:
            # CONSIDER: return None?
            raise DataExtractionError.due_to(ex, use.path, input, context)
        except Exception, ex:
            raise DataPointerError.due_to(ex, use, select)


    def wrap(self, transconfig):
        """
        wrap this Engine by a new Engine with an overriding configuration.
        """
        return Engine(transconfig, self)


    def transform(self, data):
        """
        Transform the given data against the current transform for this engine.
        """
        if not self._ct:
            self._ct = self.make_transform(self._cfg, ignorecontext=True)
        return self._ct(data, self.context)


class StdEngine(Engine):
    """
    an engine that loads the standard definitions.  
    """

    def __init__(self, context=None):
        super(StdEngine, self).__init__()
        self.load_plugin(std)
        self.load_plugin(xml)
        if context: 
            self.context = ScopedDict(self.context)
            self.context.update(context)

    def load_plugin(self, mod):
        """
        load the plugin transforms from the given python module
        """
        # load the Transform types
        self.load_transform_types(mod)

        # load the transforms
        self.load_transform_defs(mod.MOD_STYLESHEET)
        try:
            # load the context data
            self.context.update(mod.MOD_STYLESHEET['context'])
        except KeyError:
            pass

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

        

class DocEngine(Engine):
    """
    A Transformation Engine intended for loading a base stylesheet document
    and initiating the transformation.
    """

    def __init__(self, doctrans=None, context=None, sysdata=None):
        """
        create an Engine from an initial transform.  

        :argument object doctrans: the initial transform sheet
        """

        # Note that the application can override the default system context data
        ctxt = ScopedDict(DEFAULT_APP_CONTEXT)
        if context:
            ctxt = ScopedDict(ctxt)
            ctxt.update(context)

        super(DocEngine, self).__init__(doctrans, StdEngine(ctxt))
        if sysdata:
            self._system.update(sysdata)
            
    def write(self, ostrm, data, force_json=False):
        """
        transform the input data and write the output to a stream

        :argument file ostrm:  the output file stream to write the result to
        :argument json data:   the input JSON data to transform
        :argument bool force_json:  if True, always write out in JSON format.
                               Normally (False), if the output is a string, 
                               then that string will be written directly to the 
                               output stream.  When True, a string output will 
                               converted to a JSON-formatted string (with 
                               surrounding quotes.
        """
        out = self.transform(data)
        if not force_json and (isinstance(out, str) or isinstance(out, unicode)):
            ostrm.write(out)
            if out[-1] != '\n': 
                ostrm.write('\n')
        else:
            json.dump(out, ostrm, indent=self.context['json.indent'],
                      separators=(self.context['json.item_separator'],
                                  self.context['json.dict_separator']))
            ostrm.write('\n')




DEFAULT_APP_CONTEXT = {

    # When writing json documents out to a file, use this number of spaces
    # to indent complex data (array items and object properties).  A negative
    # number switches on "pretty printing".
    "json.indent": None,

    # When writing json documents out to a file, use this string to separate
    # items  
    "json.item_separator": ', ',

    # When writing json documents out to a file, use this string to separate
    # object property names from their values
    "json.dict_separator": ': '

}

DEFAULT_ENV = {

    # The python package containing contributed modules
    "$sys.contrib_pkg":  "jsont_contrib",

}
