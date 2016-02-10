"""
transformers from the standard module
"""
import os, json, copy, re, importlib, textwrap
import types as tps
import json as jsp

from ..exceptions import *
from ..base import Transform, ScopedDict
from .. import parse

MODULE_NAME = __name__

TRANSFORMS_PKG = __name__.rsplit('.', 1)[0]
DEF_CONTRIB_PKG = TRANSFORMS_PKG

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
    a transform based on a template for an output string.  It will replace 
    template tokens in the string template with strings derived from the input 
    data
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
                    if item == '' or ':' in item or item.startswith('/'):
                        # it's a pointer
                        item = Extract({ "select": item }, self.engine, 
                                       (self.name or "extract")+":(select)", 
                                       "extract")
                    else:
                        # see if it matches a transform or transform-function
                        # (may raise a TransformNotFound)
                        item = self.engine.resolve_transform(item)

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

        skel = self._resolve_skeleton(copy.deepcopy(content), engine)
        
        def impl(input, context, *args):
            return self._transform_skeleton(skel, input, context)

        return impl

    def _resolve_skeleton(self, skel, engine):
        if isinstance(skel, dict):
            if skel.has_key("$val"):
                # $val means replace the object with the output from the
                # Transform given as the value to $val
                if isinstance(skel["$val"], dict):
                    return engine.make_transform(skel["$val"], 
                                                 self.name+".(anon)")
                else:
                    item = skel['$val']
                    if item == '' or ':' in item or item.startswith('/'):
                        # it's a pointer
                        return Extract({ "select": item }, self.engine, 
                                       self.name+":(select)", "extract")

                    # else see if it matches a transform or transform-function
                    # (may raise a TransformNotFound)
                    return self.engine.resolve_transform(item)
            else:
                self._resolve_json_object(skel, engine)
        elif (isinstance(skel, str) or isinstance(skel, unicode)) and \
             "{" in skel and "}" in skel:
            skel = self._resolve_json_string(skel, engine)
        elif isinstance(skel, list) or isinstance(skel, tuple):
            self._resolve_json_array(skel, engine)

        return skel

    def _resolve_json_object(self, content, engine):
        # resolve the values
        for key in content:
            content[key] = self._resolve_skeleton(content[key], engine)

        # resolve keys
        keytrans = {}
        for key in content.keys():
            if "{" in key and "}" in key:
                keytrans[key] = self._resolve_json_string(key, engine)

        if keytrans:
            # "\bkeytr" is a special key for holding Transforms that will 
            # transform the keys.
            content["\bkeytr"] = keytrans

        return content

    def _resolve_json_array(self, content, engine):

        # resolve each item
        for i in range(len(content)):
            content[i] = self._resolve_skeleton(content[i], engine)

        return content

    def _resolve_json_string(self, content, engine):

        return StringTemplate({ "content": content, }, engine, self.name,
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

class Extract(Transform):
    """
    a transform that extracts data from the input via a data pointer
    """

    def mkfn(self, config, engine):
        select = config.get("select", '')
        def impl(input, context, *args, **keys):
            return engine.extract(input, context, select)
        return impl

class Map(Transform):
    """
    a transform that applies a specified transform to each item in the input
    array.  
    """
    def mkfn(self, config, engine):

        itemmap = config.get('itemmap', 'tostr')
        if isinstance(itemmap, dict):
            # it's an anonymous transform configuration
            itemmap = engine.make_transform(itemmap)
        else:
            itemmap = engine.resolve_transform(itemmap)

        strict = config.get('strict', False)

        def impl(input, context, *args, **keys):
            data = input
            if not isinstance(data, list):
                if not strict:
                    data = [data]
                else:
                    raise TransformInputTypeError('array', type(data), 
                                                  (self.name or "map"), data,
                                                  context)
            return map(lambda i: itemmap(i, context), data)

        return impl

class Apply(Transform):
    """
    A transform that applies another transform with different data set as the 
    current input data.  
    """
    def mkfn(self, config, engine):
        try:
            transf = config['transform']
        except KeyError:
            raise MissingTransformData("transform", self.name)
        if isinstance(transf, dict):
            transf = engine.make_transform(transf)
        elif isinstance(transf, str) or isinstance(transf, unicode):
            transf = engine.resolve_transform(transf)
        else:
            raise TransformConfigTypeError('transform', 'dict or str', 
                                           type(transf))

        newin = self._resolve_input(config.get('input', ''), transf.engine)

        targs = config.get('args', [])

        def impl(input, context, *args, **keys):
            
            usein = newin
            if isinstance(newin, Transform):
                usein = newin(input, context)
            
            useargs = targs + list(args)

            return transf(usein, context, *useargs)

        return impl

    def _resolve_input(self, input, engine):

        if isinstance(input, dict):
            # this is a transform configuration object
            return engine.make_transform(input, "(anon)")

        if not isinstance(input, str) and not isinstance(input, unicode):
            raise TransformConfigTypeError('input', 'dict or str', type(input))

        if '(' in input or ')' in input:
            return engine.resolve_transform(input)

        if input == '' or ':' in input or input.startswith('/'):
            # it's a pointer
            return Extract({ "select": input }, engine, 
                           (self.name or "extract")+":(select)", "extract")

        # see if it matches a transform or transform-function
        # (may raise a TransformNotFound)
        return engine.resolve_transform(input)


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
            fname = ".".join([TRANSFORMS_PKG, fname[1:]])
        else:
            fname = ".".join([engine._system['$sys.contrib_pkg'], fname])
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

    def mkfn(self, config, engine):
        try:
            targs = list(config['args'])
        except KeyError, ex:
            raise MissingTranformData("args", self.name)
        except TypeError, ex:
            raise TransformConfigTypeError("args", "list", type(config['args']),
                                           self._name)

        try:
            wrapped = config['transform']
            if not isinstance(wrapped, Transform):
                wrapped = engine.resolve_transform(wrapped)
        except KeyError, ex:
            raise MissingTranformData("transform", self.name)
        except TypeError, ex:
            raise TransformConfigTypeError("transform", "str", 
                                           type(config['transform']), self._name)

        uargs = targs
        if isinstance(wrapped, Callable):
            uargs = self._build_args(wrapped, targs, engine)
            args_index = wrapped.args_index
            wrapped = self._wrap_callable(wrapped, targs, engine)

        for i in range(len(uargs)):
            if isinstance(uargs[i], str) or isinstance(uargs[i], unicode):
                try:
                    # try assuming the argument is JSON data
                    if uargs[i][0] == "'" and uargs[i][-1] == "'":
                        uargs[i] = '"'+uargs[i][1:-1]+'"'

                    uargs[i] = json.loads(uargs[i])
                    if isinstance(uargs[i], str) and "{" in uargs[i]:
                        uargs[i] = StringTemplate({'content': uargs[i]}, engine, 
                                                  self.name+":(arg)", 
                                                  "stringtemplate")
                    elif isinstance(uargs[i], list) or isinstance(uargs[i],dict):
                        uargs[i] = JSON({'content': uargs[i]}, engine, 
                                        self.name+":(arg)", "json")
                                       
                except ValueError:
                    # It should be interpreted as a transform directive
                    uargs[i] = engine.resolve_transform(uargs[i])


        def impl(input, context, *eargs, **keys):
            use = []

            # execute all transform references included in argument list
            for i in range(len(uargs)):
                item = uargs[i]
                if isinstance(item, Transform):
                    item = item(input, context)
                use.append(item)

            return wrapped(input, context, *use)

        return impl

    def _wrap_callable(self, callable, args, engine):
        # extract the arguments that are used to configure the transform
        use = []
        for idx in callable.config_args_index:
            if idx >= len(args):
                msg = TransformConfigException.make_message(callable.name,
                        "Insufficient number of arguments provided")
                raise TransformConfigException(msg, callable.name)
            use.append(args[idx])
                
        # apply the arguments to the transform template
        transtmpl = callable.config_template
        transf = JSON({"content": transtmpl}, engine, 
                      callable.type+":(args)","json")
        config = transf(use, None)
        return engine.make_transform(config)

    def _build_args(self, callable, args, engine):
        # extract the arguments that are used to configure the transform
        use = []
        for idx in callable.args_index:
            if idx >= len(args):
                msg = TransformConfigException.make_message(callable.name,
                        "Insufficient number of arguments provided")
                raise TransformConfigException(msg, callable.name)
            use.append(args[idx])

        used = set(callable.args_index).union(callable.config_args_index)
        extra_index = list(set(xrange(len(args))).difference(used))
        extra_index.sort()

        for idx in extra_index:
            use.append(args[idx])

        return use


        
                


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
        config = { "args": tuple(args), "transform": transf }
        return cls(config, engine, transf+"()", "function")

    def _resolve_argstr(self, argstr):
        out = self.__class__._parse_argstr(argstr)

class FunctionSyntaxError(TransformConfigException):
    """
    an exception indicating a syntax error was detected while the parsing a 
    function invocation.  
    """

    def __init__(self, message):
        super(FunctionSyntaxError, self).__init__(message)

class Callable(Transform):
    """
    a transform that can be used to turn other Tranform types into transforms
    that can be called in function form.
    """

    @property
    def config_template(self):
        """
        a template for the configuration for the underlying transform.  This 
        contains data pointers into the array of configuration arguments that 
        are extracted (and reordered) via config_args_index.
        """
        return self._transf_config_template

    @property
    def config_args_index(self):
        """
        an ordered list of argument indexes for selecting which arguments given
        to the function should be used to configure the underlying transform at 
        resolve time.  Used by the Function Transform.  
        """
        return self._config_args_index

    @property
    def args_index(self):
        """
        an ordered list of argument indexes for selecting which arguments given
        to the function should be passed to the underlying transform at transform
        time.  Used by the Function Transform.  
        """
        return self._pass_args_index

    def mkfn(self, config, engine):
        try:
            self._transf_config_template = config['transform_tmpl']
        except KeyError:
            raise MissingTranformData("transform_tmpl", self.name)
        # check the type
        if not isinstance(self._transf_config_template, dict):
            raise TransformConfigTypeError('transform_tmpl', 'obj', 
                                           type(self._transf_config_template),
                                           self.name)

        try: 
            self._config_args_index = config['conf_args_index']
        except KeyError:
            raise MissingTranformData("conf_args_index", self.name)
        # check the type
        if not isinstance(self._config_args_index, list):
            raise TransformConfigTypeError('conf_args_index', 'obj', 
                                           type(self._config_args_index),
                                           self.name)
        bad = filter(lambda i: not isinstance(i, int), 
                     self._config_args_index)
        if len(bad):
            raise TransformConfigTypeError('conf_args_index[]', 'int', 
                                           type(bad[0]), self.name)
                                           

        self._pass_args_index = config.get('pass_args_index', [])
        # check the type
        if not isinstance(self._pass_args_index, list):
            raise TransformConfigTypeError('pass_args_index', 'list', 
                                           type(self._pass_args_index),
                                           self.name)
        bad = filter(lambda i: not isinstance(i, int), 
                     self._pass_args_index)
        if len(bad):
            raise TransformConfigTypeError('pass_args_index[]', 'int', 
                                           type(bad[0]), self.name)

        def impl(input, context):
            raise TransformApplicationException("Attempt to apply callable " +
                        "transform directly (without wrapper)")

        return impl

            
            


types = { "literal": Literal, 
          "stringtemplate": StringTemplate, 
          "native": Native,
          "map": Map,
          "json": JSON,
          "extract": Extract,
          "apply": Apply,
          "callable": Callable
          }

# function type implementations

def identity_func(engine, input, context, *args, **keys):
    """
    return the input data structure unchanged
    :returns JSON data:
    """
    return input

def tostr(engine, input, context, data=None, *args, **keys):
    """
    convert the input data into a JSON string
    :return str:
    """
    if not data:
        data = input

    if isinstance(data, str):
        return data
    return jsp.dumps(data)


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

def wrap(engine, input, context, maxlen=75, text=None, *args, **keys):
    """
    convert a paragraph of text into an array of strings broken at word 
    boundarys that are less than a given maximum in length.  
    """
    if not text:
        text = input

    if not isinstance(text, str) and not isinstance(text, unicode):
        raise TransformInputTypeError("string", str(type(text)), "wrap", 
                                      input, context)
    if not isinstance(maxlen, int):
        raise TransformInputTypeError("integer", str(type(maxlen)), "wrap", 
                                      maxlen, context)

    return textwrap.wrap(text, maxlen)

def indent(engine, input, context, indlen=4, text=None, *args, **keys):
    """
    prepend a specified number of spaces in front of the input text.
    """
    if not text:
        text = input

    if not isinstance(text, str) and not isinstance(text, unicode):
        raise TransformInputTypeError("string", str(type(text)), "indent", 
                                      input, context)
    if not isinstance(indlen, int):
        raise TransformInputTypeError("integer", str(type(indlen)), "indent", 
                                      indlen, context)
    return (indlen * ' ') + text




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

# load in stylesheet-based definitions 

MOD_STYLESHEET_FILE = "std_ss.json"

ssfile = os.path.join(os.path.dirname(__file__), MOD_STYLESHEET_FILE)
with open(ssfile) as fd:
    MOD_STYLESHEET = jsp.load(fd)
del ssfile

# load the module's initial context data.  The defaults are specified here 
# for documentation purposes; however, values set wihtin the stylesheet file 
# will take precedence.

p = "std."

def_context = {

    # The prefered line width to use when filling data into paragraphs by 
    # the fill transform
    #
    p+"fill.width": 75,

    # The prefered indentation amount to use when filling data into 
    # paragraphs by the fill transform
    # 
    p+"fill.indent": 0,
}
del p

# the module's default context data
MOD_CONTEXT = ScopedDict(def_context)
MOD_CONTEXT.update(MOD_STYLESHEET.get('context',{}))
MOD_STYLESHEET['context'] = MOD_CONTEXT

