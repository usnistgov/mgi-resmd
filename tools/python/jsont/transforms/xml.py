"""
transforms for creating XML from JSON data
"""
import os, json, copy, re

from ..exceptions import *
from ..base import Transform, ScopedDict
from .std import JSON, Extract

MODULE_NAME = __name__
TRANSFORMS_PKG = __name__.rsplit('.', 1)[0]

class ElementContent(object):
    """
    a representation of complex element content including an element's 
    attributes and children (but not it's name).  It's data is packaged
    as JSON data.
    """

    def __init__(self, data=None):
        self.data = data
        if self.data is None:
            self.data = {}

    @property
    def attributes(self):
        if not self.data.has_key('attrs'):
            self.data['attrs'] = []
        return self.data['attrs']

    def add_attribute(self, attr):
        """
        append an attribute definition
        """
        self.attributes.append(attr)

class Attribute(object):
    """
    a representation of an XML attribute.  It's data is packaged
    as JSON data.
    """

    def __init__(self, data):
        if data is None:
            raise ValueError("None provided as attribute data")
        self.data = data

        missing = []
        for prop in "name value".split():
            if prop not in self.data:
                missing.append(prop)
        if len(missing) > 0:
            raise ValueError("dictionary contents does not look like an " +
                             "attribute (missing " + str(missing) + 
                             "): "+str(self.data))

    @classmethod
    def create(cls, name, value, prefix=None, ns=None):
        data = {"name": name, "value": value }
        if prefix is not None:
            data['prefix'] = prefix
        if ns is not None:
            data['namespace'] = ns

        return cls(data)

############

class ToAttribute(Transform):

    def mkfn(self, config, engine):
        try:
            name = config['name']
        except KeyError, ex:
            raise MissingTransformData("name", self.name)
        try:
            value = config['value']
        except KeyError, ex:
            raise MissingTransformData("value", self.name)

        if isinstance(name, str)
          if '{' in name and '}' in name:
            name = StringTemplate({'content': name}, engine, 
                                  (self.name or 'attr')+" name", "xml.attribute")
        elif isinstance(name, dict):
            


class ToElementContent(Transform):

    def mkfn(self, config, engine):
        attrs = None
        if config.has_key("attrs"):
            if not isinstance(config['attrs'], list):
                raise TransformConfigTypeError("attrs", "array", 
                                               type(config['attrs']), 
                                               "elementContent")
            attrs = []
            for attr in config['attrs']:
                if isinstance(attr, dict):
                    # it's an object, either a transform or JSON template
                    if not attr.has_key('$val'):
                        # it's a JSON template
                        attr = JSON({'content': attr}, engine, 
                                    "{0} attr".format((self.name or '')),
                                    "elementContent")
                    else:
                        attr = attr["$val"]

                if isinstance(attr, dict):
                    # it's an anonymous transform
                    attr = engine.make_transform(attr)

                elif isinstance(attr, str) or isinstance(attr, unicode):
                    if attr == '' or ':' in attr or attr.startswith('/'):
                        # it's a data pointer to select data
                        attr = Extract({'select': attr}, engine,
                                       "{0} attr".format((self.name or '')),
                                       "elementContent")
                    else:
                        # it's a named transform or transform function
                        attr = engine.resolve_transform(attr)

                attrs.append(attr)
        
        children = None
        if config.has_key("children"):
            if isinstance(config['children'], str) or \
               isinstance(config['children'], unicode):
                children = [children]

            if not isinstance(config['children'], list):
                raise TransformConfigTypeError("children", "array or string", 
                                               type(config['children']), 
                                               "elementContent")

            children = []
            for child in config['children']:
                if isinstance(child, str) or isinstance(child, unicode):
                    # assume it's a string template
                    child = StringTemplate({'content': child}, engine, 
                                          "{0} child".format((self.name or '')),
                                            "elementContent")
                elif isinstance(child, dict):
                    # it's an object, either a transform or JSON template
                    if not child.has_key('$val'):
                        # it's a JSON template
                        child = JSON({'content': child}, engine, 
                                    "{0} child".format((self.name or '')),
                                    "elementContent")
                    else:
                        child = child["$val"]

                if isinstance(child, dict):
                    # it's an anonymous transform
                    child = engine.make_transform(child)

                elif isinstance(child, str) or isinstance(child, unicode):
                    if child == '' or ':' in child or child.startswith('/'):
                        # it's a data pointer to select data
                        child = Extract({'select': child}, engine,
                                        "{0} child".format((self.name or '')),
                                        "elementContent")
                    else:
                        # it's a named transform or transform function
                        child = engine.resolve_transform(child)

                children.append(child)
        
        def impl(input, context, *args):
            out = {}
            if attrs is not None:
                ol = []
                for attr in attrs:
                    if isinstance(attr, Transform):
                        attr = attr(input, context)
                    ol.append(attr)
                out['attrs'] = ol

            if children is not None:
                ol = []
                for child in children:
                    if isinstance(child, Transform):
                        attr = child(input, context)
                    ol.append(child)
                out['children'] = ol

            return out

        return impl
