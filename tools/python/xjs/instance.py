"""
a module for interacting with JSON instances that leverage features of 
extended JSON schemas
"""
from __future__ import with_statement

import os, json, jsonspec.pointer
from urlparse import urlparse
from urllib2 import urlopen

EXTSCHEMAS = "$extensionSchemas"

class Instance(object):
    """
    a class that helps interact with JSON instances that leverage features 
    of extended JSON schemas
    """

    def __init__(self, data, srcloc=None, srcid=None, jptr="/"):
        """
        initialize the Instance wrapper

        :argument obj data:    the JSON data to wrap
        :argument str srcloc:  the file location that was the source of the 
                                  JSON data.  This can be a URL or a string 
                                  representing a file path from accessible 
                                  disk.  If not provided, the source is 
                                  unknown.
        :argument str srcid:   the URI that identifies the data contained in 
                                  the source file as a whole.  (This is not 
                                  necessarily, then, the identifier for the 
                                  particular given data unless the data 
                                  represents the full contents of the file.)
                                  If not provided and jptr is "/" (or an empty
                                  string), this constructor will attempt to 
                                  set it by looking at the top "id" property, 
                                  if it exists.  Otherwise, the source is 
                                  unknown.
        :argument str jptr:    the JSON Pointer within the source file that 
                                  points to the given data.  If not given, it 
                                  can be assumed that the pointer is "/".  
        """
        self.data = data
        self._srcid = srcid
        self._srcloc = srcloc
        self._ptr = jptr

        if isinstance(self.data, dict):
            if not self._srcid:
                self._srcid = self.data.get('id')

    @classmethod
    def from_location(cls, loc):
        """
        Open the source location (either a file or a URL) and load its
        JSON data into an Instance instance
        """
        data = None
        url = urlparse(loc)

        # Note: this part adapted from jsonschema.RefResolver.resolve_remote()
        # (v2.5.1)
        if not url.scheme:
            # it's a file
            with open(loc) as fd:
                data = json.load(fd)
        elif (
            scheme in [u"http", u"https"] and
            requests and
            getattr(requests.Response, "json", None) is not None
        ):
            # Requests has support for detecting the correct encoding of
            # json over http
            if callable(requests.Response.json):
                data = requests.get(loc).json()
            else:
                data = requests.get(loc).json
        else: 
            # Otherwise, pass off to urllib and assume utf-8
            data = json.loads(urlopen(uri).read().decode("utf-8"))

        return Instance(data, loc)



    @property
    def source_location(self):
        """
        the location of the file that was the source of the wrapped data.
        This can be a URL or a file path.
        """
        return self._srcloc

    @property 
    def source_id(self):
        """
        the URI for the full data contained in the file that the wrapped 
        data was extracted from.
        """
        return self._srcid

    @property
    def pointer(self):
        """
        the JSON Pointer to the wrapped data relative to the source file
        """
        return self._ptr

    def find_data_by_name(self, name):
        """
        return a list of pointer-value tuples that match a given name.  

        The function will walk through the data tree looking for occurances 
        of the given name as an object property.  For each matching property 
        found, the function will return as an element of the returned list 
        the JSON Pointer to the property and the property's value.  The 
        returned pointers are assumed to be relative to the pointer to the set
        pointer of the wrapped data object.  Note that the last token in the 
        returned pointer will be the given name.  
        """
        out = []
        self._find_prop_by_name(name, self.data, out)
        return out

    def _find_prop_by_name(self, name, data, out, path=""):
        if isinstance(data, dict):
            if data.has_key(name):
                out.append( ("/".join((path,name)), data[name]) )

            for prop in data:
                self._find_prop_by_name(name, data[prop], out, 
                                        "/".join([path,prop]))

        if isinstance(data, list):
            for i in xrange(len(data)):
                self._find_prop_by_name(name, data[i], out, 
                                        "/".join([path,str(i)]))

    def _find_obj_by_prop(self, name, data, out, path=""):
        if isinstance(data, dict):
            if data.has_key(name):
                out.append( (path or "/", data) )

            for prop in data:
                self._find_obj_by_prop(name, data[prop], out, 
                                       "/".join([path,prop]))

        if isinstance(data, list):
            for i in xrange(len(data)):
                self._find_obj_by_prop(name, data[i], out, 
                                       "/".join([path,str(i)]))

    def find_obj_by_prop(self, name):
        """
        return a list of pointer-object tuples that contain a property having
        the given name

        The function will walk through the data tree looking for occurances 
        of the given name as an object property.  For each matching property 
        found, the function will return as an element of the returned list 
        the JSON Pointer to the object cotaining the property and the object 
        itself.  The returned pointers are assumed to be relative to the 
        pointer to the set pointer of the wrapped data object.   
        """
        out = []
        self._find_obj_by_prop(name, self.data, out)
        return out

    def find_extended_objs(self):
        """
        return a list of pointer-object tuples that containing the 
        "$extensionSchemas" property.
        
        This function is equivalent to 
        self.find_obj_by_prop("$extensionSchemas").  That is, it returns all
        objects (including the root object, if applicable) that contains 
        the "$exensionSchemas" property.  
        """
        return self.find_obj_by_prop(EXTSCHEMAS)

    def extract(self, jptr):
        """
        return the data pointed to by given JSON Pointer
        """
        return jsonspec.pointer.extract(self.data, jptr)

