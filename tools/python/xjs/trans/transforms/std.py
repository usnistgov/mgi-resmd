"""
transformers from the standard module
"""
import json, copy, re
import types as tps
import json as jsp

from ..exceptions import *
from ..base import Transform

joins = [ "concat", "delim" ]
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
    _braces_re = re.compile("([\{\}])")

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

        # break up string at the braces
        parts = self._braces_re.split(content)

        # collapse template tokens with their surrounding braces
        depth = 0
        parsed = []
        for i in range(len(parts)):
            item = parts[i]
            parsed.append(item)
            if item == '{':
                depth += 1
                if depth == 1:
                    first = len(parsed)-1
            elif item == '}':
                depth -= 1
                if depth < 0:
                    raise StringTemplateSyntaxError("No matching { for }",
                                                    ["".join(parsed), item, 
                                                     "".join(parts)], content,
                                                    self.name)
                if depth == 0:
                    parsed[first:] = [ "".join(parsed[first:]) ]

        # resolve the tokens into transforms
        if '{' in parts:
            for i in range(len(parsed)):
                item = parsed[i]
                if item.startswith('{'):
                    item = item[1:-1]
                    try:
                        # see if it matches a template or template-function
                        item = self.engine.resolve_template(item)
                    except TransformNotFound:
                        # it's a pointer
                        item = Pointer({ "select": item }, self.engine, 
                                       self.name+":(select)", "pointer")
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
        
        def impl(input, *args):
            newdata = copy.deepcopy(skel)
            self._transform_skeleton(newdata, engine, input, context)
            return newdata

        return impl

    def _resolve_skeleton(self, skel):
        if isinstance(content, dict):
            if content.has_key("$val"):
                if isinstance(content["$val"], dict):
                    return self.engine.make_transform(content["$val"], 
                                                      self.name+".(anon)")
                else:
                    return self.engine.resolve_transform(content["$val"])
            else:
                _resolve_json_object(skel)
        elif isinstance(content, str) and "{" in content and "}" in content:
            content = _resolve_json_string(skel)
        elif isinstance(content, list) or isinstance(content, tuple):
            _resolve_json_array(skel)

        return skel

    def _resolve_json_object(self, content):
        # resolve the values
        for key in content:
            _resolve_skeleton(content[key])

        # transform keys
        for key in content.keys():
            if "{" in key and "}" in key:
                newkey = _transform_json_string(key)
                content[newkey] = content.pop(key)

        return content

    def _resolve_json_array(self, content):

        # resolve each item
        for i in range(len(content)):
            content[i] = _resolve_skeleton(content[i])

        return content

    def _resolve_json_string(self, content):

        return StringTemplate({ "content": content, }, self.engine, self.name,
                              type="stringtemplate")

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
        join = config.get('join')
        if join:
            join = self.engine.resolve_template(join)
        else:
            join = concat

        def impl(input, context, *args, **keys):
            items = map(lambda i: itemmap(engine, i, context), input)
            return join(engine, items, context)
        return impl

class Pointer(Transform):
    """
    a transform that extracts data from the input via a data pointer
    """

    def mkfn(self, config, engine):
        select = config.get("select", '')
        def impl(input, context, *args, **keys):
            return extract(engine, input, context, select)
        return impl

class Function(Transform):
    """
    a transform that produces its output by calling a configured function
    """

    def mkfn(self, config, engine):
        try: 
            fname = config['name']
        except KeyError:
            raise MissingTranformData("content", "json")

        if fname.startswith('$'):
           fname = ".".join([TRANSFORMS_MOD, fname[1:]])
        fimpl = self._load_function(fname[1:]) #throws exc for unresolvable func

        confargs = config.get('args', [])

        def impl(input, context, *args, **keys):
            use = confargs + args
            return fimpl(self.engine, input, context, *use, **keys)
        return impl

    def _load_function(fname):
        try: 
            (mod, fname) = fname.rsplit('.', 1)
            mod = importlib.import_module(mod)
            return getattr(mod, fname)
        except ValueError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
                                   "function name is missing module prefix"))
        except ImportError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
                                         "function not found with this name"))
        except AttributeError, ex:
            raise TransformConfigParamError("name", self.name, 
                  TransformConfigException.make_message(self.name, 
               "function {0} not found in the {1} module".format(fname, mod)))
            

types = { "literal": Literal, 
          "stringtemplate": StringTemplate, 
          "function": Function,
          "mapjoin": MapJoin,
          "json": JSON
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

def wrap(engine, input, context, maxlen, *args, **keys):
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
    use = _prep_array_for_join(input, name, input, context)
    return delim.join(use)

