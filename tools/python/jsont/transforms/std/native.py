"""
This module provides implementations of native-type transforms
"""
import json, textwrap
import json as jsp

from ...exceptions import *


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


def tobool(engine, input, context, data=complex(1,1), *args, **keys):
    """
    convert the input data into a JSON boolean.
    :return str:
    """
    if isinstance(data, complex):
        data = input

    if isinstance(data, bool):
        return data

    if isinstance(data, (str, dict, tuple, list)):
        return len(data) > 0
    if isinstance(data, (int, long, float)):
        return data != 0
    return data is not None


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

def prop_names(engine, input, context, *args):
    """
    return an array containing the names of the properties in the input
    object.
    """
    if isinstance(input, dict):
        return input.keys()

    return []

def metaprop(engine, input, context, *args):
    """
    return the given string prepended with a $ symbol.  This allows one 
    to produce a meta property name without invoking its special meeting within
    a transform.  The input and context data are ignored if an argument is 
    provided. 
    """
    out = "$"
    if len(args) > 0:
        out += str(args[0])
    else:
        out += str(input)
    return out

def isdefined(engine, input, context, select=None, *args):
    """
    return True if the data pointed to by a selection is defined.

    :argument str select:  a data pointer refering to a specific node into 
                           either the input or context data whose type is of
                           interest.  If not provided, the input data as a 
                           whole ($in:) is assumed.
    """
    if select:
        try:
            input = engine.extract(input, context, select)
        except DataExtractionError:
            return False
    return True

def istype(engine, input, context, type, select=None, *args):
    """
    return True if the data pointed to by a selection is a JSON data 
    structure of a given type.
    If data pointed to by the selection does not exist, False is returned.

    :argument str type:  the name of the JSON type being tested against.  It 
                           must be one of 'object', 'array', 'string', 'boolean',
                           'number', 'integer', or 'null'; otherwise, False is 
                           returned.
    :argument str select:  a data pointer refering to a specific node into 
                           either the input or context data whose type is of
                           interest.  If not provided, the input data as a 
                           whole ($in:) is assumed.
    """
    if select:
        try:
            input = engine.extract(input, context, select)
        except DataExtractionError:
            return False
    if type == "object":
        return isinstance(input, dict)
    if type == "array":
        return isinstance(input, (list, tuple))
    if type == "string":
        return isinstance(input, (str, unicode))
    if type == "number":
        return isinstance(input, (int, long, float))
    if type == "integer":
        return isinstance(input, int)
    if type == "boolean":
        return isinstance(input, bool)
    if type == "null":
        return input is None
    return False

