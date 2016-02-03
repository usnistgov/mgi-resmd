"""
transformers from the standard module
"""
import json, copy, re, importlib
import types as tps
import json as jsp

from ..exceptions import *
from ..base import Transform
from .. import parse

joins = [ "delim" ]
transforms = [ "identity_function", "applytransform", "extract", "wrap" ]
templates = [ "tostr" ]

TRANSFORMS_MOD = __name__.rsplit('.', 1)[0]

# Transform types:

class Literal(Transform):
    """
    a transform type that returns a constant value.
    """
    def mkfn(self, config, engine):
        val = config.get("value", "")
        def impl(input, context, *args):  
            assert self.engine
            return val
        return impl

class StringTemplate(Transform):
    """
    a template that will replace template tokens in a string
    with strings derived from the input data
    """

    def mkfn(self, config, engine):

        try: 
            content = config['content']
        except KeyError:
            raise MissingTranformData("content", self.name)
        if not isinstance(content, str) and not isinstance(content, unicode):
            raise TransformConfigTypeError("content", "str", type(content), 
                                           self.name)

        parsed = self.parse_template_str(content)

        def impl(input, context, *args, **keys):
            out = []

            # execute all embedded transforms
            for i in range(len(parsed)):
                item = parsed[i]
                if isinstance(item, Transform):
                    item = item(input, context)
                    if not isinstance(item, str) and not isinstance(item, unicode):
                        item = jsp.dumps(item)
                out.append(item)

            return "".join(out)
        return impl

    def parse_template_str(self, content):

        parsed = []
        while len(content) > 0:
            i = content.find('{')
            if i < 0:
                parsed.append(content)
                content = ''
                continue

            if i > 0:
                parsed.append(content[0:i])
                content = content[i:]

            try:
                tok, content = parse.chomp_br_enclosure(content)
                parsed.append(tok)
            except parse.ConfigSyntaxError:
                # no closing brace; treat like a normal string
                if not parsed:
                    parsed.append(content[0])
                else:
                    parsed[-1] += content[0]
                content = content[1:]


        # resolve the tokens into transforms
        if len(filter(lambda p: p.startswith('{') and p.endswith('}'),parsed)) >0:
            for i in range(len(parsed)):
                item = parsed[i]
                if item.startswith('{') and item.endswith('}'):
                    item = item[1:-1]
                    try:
                        # see if it matches a template or template-function
                        item = self.engine.resolve_template(item)
                    except TransformNotFound:
                        # it's a pointer
                        item = Extract({ "select": item }, self.engine, 
                                       self.name+":(select)", "extract")
                    parsed[i] = item

        return parsed

class JSON(Transform):
    """
    a Transform that converts the input data to a new JSON structure.
    """

    def mkfn(self, config, engine):
        try: 
            content = config['content']
        except KeyError:
            raise MissingTranformData("content", self.name)

        skel = self._resolve_skeleton(copy.deepcopy(content))
        
        def impl(input, context, *args):
            return self._transform_skeleton(skel, input, context)

        return impl

    def _resolve_skeleton(self, skel):
        if isinstance(skel, dict):
            if skel.has_key("$val"):
                # $val means replace the object with the output from the
                # Transform given as the value to $val
                if isinstance(skel["$val"], dict):
                    return self.engine.make_transform(skel["$val"], 
                                                      self.name+".(anon)")
                else:
                    try:
                        return self.engine.resolve_transform(skel["$val"])
                    except TransformNotFound:
                        return Extract({"select": skel["$val"]}, self.engine,
                                       self.name+":(select)", "extract")
            else:
                self._resolve_json_object(skel)
        elif (isinstance(skel, str) or isinstance(skel, unicode)) and \
             "{" in skel and "}" in skel:
            skel = self._resolve_json_string(skel)
        elif isinstance(skel, list) or isinstance(skel, tuple):
            self._resolve_json_array(skel)

        return skel

    def _resolve_json_object(self, content):
        # resolve the values
        for key in content:
            content[key] = self._resolve_skeleton(content[key])

        # resolve keys
        keytrans = {}
        for key in content.keys():
            if "{" in key and "}" in key:
                keytrans[key] = self._resolve_json_string(key)
                #newkey = _transform_json_string(key)
                #content[newkey] = content.pop(key)

        if keytrans:
            # "\bkeytr" is a special key for holding Transforms that will 
            # transform the keys.
            content["\bkeytr"] = keytrans

        return content

    def _resolve_json_array(self, content):

        # resolve each item
        for i in range(len(content)):
            content[i] = self._resolve_skeleton(content[i])

        return content

    def _resolve_json_string(self, content):

        return StringTemplate({ "content": content, }, self.engine, self.name,
                              type="stringtemplate")

    def _transform_skeleton(self, skel, input, context):
        if isinstance(skel, Transform):
            return skel(input, context)

        if isinstance(skel, dict):
            if skel.has_key("$val"):
                # $val means replace the object with the output from the
                # Transform given as the value to $val
                if isinstance(skel['$val'], Transform):
                    return skel['$val'](input, context)
                else:
                    return skel['$val']

            return self._transform_json_object(skel, input, context)

        if isinstance(skel, list) or isinstance(skel, tuple):
            return self._transform_json_array(skel, input, context)

        return skel

    def _transform_json_object(self, skel, input, context):
        out = {}

        # transform the values
        for key in skel:
            if key == "\bkeytr":
                continue
            out[key] = self._transform_skeleton(skel[key], input, context)

        # transform any keys needing transforming
        if skel.has_key("\bkeytr"):
            # "\bkeytr" is a special key for holding Transforms that will 
            # transform the keys.
            for key in skel["\bkeytr"]:
                newkey = skel["\bkeytr"][key](input, context)
                out[newkey] = out.pop(key)

        return out

    def _transform_json_array(self, skel, input, context):

        out = []

        # transform each item
        for i in range(len(skel)):
            if isinstance(skel[i], Transform):
                out.append(skel[i](input, context))
            else:
                out.append(self._transform_skeleton(skel[i], input, context))

        return out



class MapJoin(Transform):
    """
    a transform that converts an array into a single string by applying the 
    same processing on each element to create an array of strings and then join 
    them into a single string as prescribed by the configuration.
    """
    def mkfn(self, config, engine):

        itemmap = config.get('itemmap')
        if itemmap:
            itemmap = self.engine.resolve_template(itemmap)
        else:
            itemmap = tostr
        join = config.get('join', 'concat')
        join = self.engine.resolve_template(join)

        def impl(input, context, *args, **keys):
            items = map(lambda i: itemmap(engine, i, context), input)
            return join(engine, items, context)
        return impl

class Extract(Transform):
    """
    a transform that extracts data from the input via a data pointer
    """

    def mkfn(self, config, engine):
        select = config.get("select", '')
        def impl(input, context, *args, **keys):
            return extract(engine, input, context, select)
        return impl

class Native(Transform):
    """
    a transform that produces its output by calling a configured function
    """

    def mkfn(self, config, engine):
        try: 
            fname = config['impl']
        except KeyError:
            raise MissingTranformData("impl", self.name)

        if fname.startswith('$'):
           fname = ".".join([TRANSFORMS_MOD, fname[1:]])
        fimpl = self._load_function(fname) #throws exc for unresolvable func

        # configuration may provide a portion of the arguments supported by 
        # the underlying implementation
        conf_args = list(config.get('args',[]))

        def impl(input, context, *args, **keys):
            use = conf_args + list(args)
            return fimpl(self.engine, input, context, *use, **keys)
        return impl

    def _load_function(self, funcname):
        try: 
            (mod, fname) = funcname.rsplit('.', 1)
            mod = importlib.import_module(mod)
            return getattr(mod, fname)
        except ValueError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
                                   "function name is missing module prefix"))
        except ImportError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
                                         "function not found with this name: "+
                                                        funcname))
        except AttributeError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
               "function {0} not found in the {1} module".format(fname, mod)))

class Function(Transform):
    """
    a transform that wraps another (Native, typically) Transform to handle 
    an invocation in function form.  

    String templates can contain transform directives that have the form of 
    a function call--e.g. "delimit(',')".  This implies that there is a 
    transform called "delimit" that can take at least one argument.  Arguments
    themselves can be in the form of JSON data or string templates that can 
    contain transform directives.  This transform will resolve all the argument
    values and hold them until they can be applied to the input data and then
    passed to the underlying implementation.
    """

    def __init__(self, engine, transform, args, name=None, type="function"):
        self._wrapped = transform
        self._args = args
        super(Function, self).__init__({"args": tuple(args), 
                                        "transform": transform}, 
                                       engine, name, type)

    def mkfn(self, config, engine):
        if not config.has_key('args'):
            raise MissingTranformData("arg", self.name)

        if not isinstance(self._wrapped, Transform):
            self._wrapped = engine.resolve_transform(self._wrapped)

        for i in range(len(self._args)):
            arg = self._args[i]
            if isinstance(arg, str) or isinstance(arg, unicode):
                try:
                    # try assuming the argument is JSON data
                    if arg[0] == "'" and arg[-1] == "'":
                        arg = '"'+arg[1:-1]+'"'

                    arg = json.loads(arg)
                    if isinstance(arg, str) and "{" in arg:
                        arg = StringTemplate({'content': arg}, engine, 
                                             self.name+":(arg)", 
                                             "stringtemplate")
                    elif isinstance(arg, list) or isinstance(arg, dict):
                        arg = JSON({'content': arg}, engine, self.name+":(arg)",
                                   "json")
                except ValueError:
                    # It should be interpreted as a transform directive
                    arg = engine.resolve_transform(arg)

                self._args[i] = arg

        def impl(input, context, *args, **keys):
            use = []

            # execute all transform references included in argument list
            for i in range(len(self._args)):
                item = self._args[i]
                if isinstance(item, Transform):
                    item = item(input, context)
                use.append(item)

            return self._wrapped(input, context, *use)

        return impl

    @classmethod
    def matches(cls, invoc):
        """
        return True if the input string matches the function form of a transform
        invocation.  If True, it can be turned into a Function Transform via
        the factory method, parse().
        """
        return bool(parse.FUNC_PAT.search(invoc.strip()))

    @classmethod
    def parse(cls, engine, funcstr, name=None):
        """
        return a Function Transform by parsing the given function invocation 
        string.
        """
        transf, args = parse.parse_function(funcstr.strip())
        return cls(engine, transf, args, name=transf+"()")

    def _resolve_argstr(self, argstr):
        out = self.__class__._parse_argstr(argstr)

class FunctionSyntaxError(TransformConfigException):
    """
    an exception indicating a syntax error was detected while the parsing a 
    function invocation.  
    """

    def __init__(self, message):
        super(FunctionSyntaxError, self).__init__(message)

types = { "literal": Literal, 
          "stringtemplate": StringTemplate, 
          "native": Native,
          "mapjoin": MapJoin,
          "json": JSON,
          "extract": Extract
          }

# function type implementations

def identity_func(engine, input, context, *args, **keys):
    """
    return the input data structure unchanged
    :returns JSON data:
    """
    return input

def tostr(engine, input, context, *args, **keys):
    """
    convert the input data into a JSON string
    :return str:
    """
    if isinstance(input, str):
        return input
    return jsp.dumps(input)


def applytransform(engine, input, context, transform, select, *args, **keys):
    """
    apply the given transform to selected data from the input.

    :argument transform: the description of the transform to apply as either 
                         a dictionary or a string.  If a string, 
    :argument str select:  a data-pointer string
    """
    newin = engine.extract(input, context, select)
    transfunc = engine.resolve_transform(transform)
    if keys:
        context = context.default_to(keys)

    return transfunc(engine, newin, context)

def extract(engine, input, context, select, *args, **keys):
    """
    return the data pointed to by the given select data-pointer
    :argument str select:  a data-pointer string for data to extract from input
    """
    return engine.extract(input, context, select)

def wrap(engine, input, context, maxlen=75, *args, **keys):
    """
    convert a paragraph of text into an array of strings broken at word 
    boundarys that are less than a given maximum in length.  
    """
    if not isinstance(input, str):
        raise TransformInputTypeError("string", str(type(input)), "wrap", 
                                      input, context)
    return text.wrap(input, maxlen)


## join transforms

def _prep_array_for_join(ary, name, input, context):
    if not isinstance(input, list):
        raise TransformInputTypeError("array", str(type(input)), name, 
                                      input, context)
    use = []
    for item in input:
        if not isinstance(item, str) and not isinstance(item, unicode):
            item = jsp.dumps(item)
        use.append(item)

    return use

def delimit(engine, input, context, delim=", ", *args, **keys):
    """
    join the input array with a delimiter
    """
    use = _prep_array_for_join(input)
    return delim.join(use)

def _prep_array_for_join(data):
    if isinstance(data, str) or isinstance(data, unicode):
        return [data]

    if isinstance(data, list):
        out = []
        for item in data:
            if not isinstance(item, str) and not isinstance(item, unicode):
                item = json.dumps(item)
            out.append(item)

        return out

    if isinstance(data, dict):
        return [json.dumps(data)]

    return [str(data)]

            
