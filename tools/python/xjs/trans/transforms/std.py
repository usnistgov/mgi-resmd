"""
transformers from the standard module
"""
import json, copy, re
import types as tps
import json as jsp

from ..exceptions import *

types = [ "literal", "stringtemplate", "function", "mapjoin", "json" ]
joins = [ "concat", "delim" ]
transforms = [ "identity_function", "applytransform", "extract", "wrap" ]
templates = [ "tostr" ]

## function factories for different transform types

def literal(engine, config):
    """
    return a function that will return a configured value.

    This is used to implement constant templates (like $lb and $rb).  
    """
    val = config.get("value", "")
    def impl(engine, input, context, *args):  return val
    return impl

_braces_re = re.compile("([\{\}])")

def stringtemplate(engine, config):
    """
    return a function that will replace template tokens in a string
    with strings derived from the input data
    """
    try: 
        content = config['content']
    except KeyError:
        raise MissingTranformData("content", "stringtemplate")
    if not isinstance(content, str) and not isinstance(content, unicode):
        raise TransformConfigTypeError("content", "str", type(content), 
                                       "stringtemplate")

    parts = _braces_re.split(content)
    depth = 0
    parsed = []
    open = None
    for i in range(len(parts)):
        item = parts[i]
        parsed.append(item)
        if item == '{':
            depth += 1
            open = None
            if depth == 1:
                first = len(parsed)-1
        elif item == '}':
            depth -= 1
            if depth < 0:
                raise StringTemplateSyntaxError("No matching { for }",
                                                ["".join(parsed), item, 
                                                 "".join(parts)], "content",
                                                "stringtemplate")
            if depth == 0:
                parsed[first:] = [ "".join(parsed[first:]) ]
    if '{' in parts:
        for i in range(len(parsed)):
            item = parsed[i]
            if item.startswith('{'):
                item = item[1:-1]
                try:
                    # see if it matches a template or template-function
                    item = engine.resolve_template(item)
                except TransformNotFound:
                    # it's a pointer
                    item = pointer(engine, { "select": item })
                parsed[i] = item

    def impl(engine, input, context, *args, **keys):
        out = []
        for i in range(len(parsed)):
            item = parsed[i]
            if isinstance(item, tps.FunctionType):
                item = item(engine, input, context)
                if not isinstance(item, str) and not isinstance(item, unicode):
                    item = jsp.dumps(item)
            out.append(item)
        return "".join(out)
    return impl

def json(engine, config):
    """
    return a function that converts the input data to a new JSON structure.
    """
    try: 
        content = config['content']
    except KeyError:
        raise MissingTranformData("content", "json")

    def impl(engine, input, *args):
        newdata = copy.deepcopy(content)
        _transform_json(newdata, engine, input, context)
        return newdata

    return impl

def _transform_json(content, engine, input, context):
    if isinstance(content, dict):
        _transform_json_object(content, engine, input, context)
    elif isinstance(content, str) and "{" in content and "}" in content:
        content = _transform_json_string(content, engine, input, context)
    elif isinstance(content, list) or isinstance(content, tuple):
        _transform_json_array(content, engine, input, context)

    return content

def _transform_json_object(content, engine, input, context):

    # transform values
    for key in content:
        _transform_json(content[key], engine, input, context)

    # transform keys
    for key in content.keys():
        if "{" in key and "}" in key:
            newkey = _transform_json_string(key, engine, input, context)
            content[newkey] = content.pop(key)

    return content

def _transform_json_array(content, engine, input, context):

    for i in range(len(content)):
        content[i] = _transform_json(content[i])

    return content

def _transform_json_string(engine, input, context):
    pass

def mapjoin(engine, config):
    """
    transform an array into a single string by applying the same processing 
    on each element to create an array of strings and then join them into a 
    single string as prescribed by the configuration.
    """
    itemmap = config.get('itemmap')
    if itemmap:
        itemmap = engine.resolve_template(itemmap)
    else:
        itemmap = tostr
    join = config.get('join')
    if join:
        join = engine.resolve_template(join)
    else:
        join = concat

    def impl(engine, input, context, *args, **keys):
        items = map(lambda i: itemmap(engine, i, context), input)
        return join(engine, items, context)

def pointer(engine, config):
    select = config.get("select", '')
    def impl(engine, input, context, *args, **keys):
        return extract(engine, input, context, select)
    return impl

def function(engine, config):
    """
    provide a function that will call a named function as its implementation
    """
    try: 
        fname = config['name']
    except KeyError:
        raise MissingTranformData("content", "json")

    if fname.startswith('$'):
       fname = TRANSFORMS_MOD + fname[1:]
       fimpl = _load_function(fname)      # throws exc for unresolvable func

    confargs = config.get('args', [])

    def impl(engine, input, context, *args, **keys):
        use = confargs + args
        return fimpl(engine, input, context, *use, **keys)
    return impl


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

