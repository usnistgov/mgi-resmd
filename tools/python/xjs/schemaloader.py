"""
a module that provides support for loading schemas, particularly those 
cached on local disk.  
"""
from __future__ import with_statement
import sys, os, json, errno

from urlparse import urlparse
from urllib2 import urlopen
from collections import Mapping
import jsonschema as jsch

from .location import read_loc_file

try:
    import requests
except ImportError:
    requests = None

SCHEMA_LOCATION_FILE = "schemaLocation.json"

class BaseSchemaLoad(object):

    def load_schema(self, uri):
        """
        return the parsed json schema document for a given URI.

        :exc `KeyError` if the location of the schema has not been set
        :exc `IOError` if an error occurs while trying to read from the 
                       registered location.  This includes if the file is
                       not found or reading causes a syntax error.  
        """
        raise NotImplementedError("Programmer error: load_schema() "+
                                  "not implemented")

    def __call__(self, uri):
        """
        return the parsed json schema document for a given URI.  Calling an
        instance as a function is equivalent to calling load_schema().
        """
        return self.load_schema(uri)

class SchemaLoader(BaseSchemaLoad):
    """
    A class that can be configured to load schemas from particular locations.
    For example, it can be used as a schema handler that loads schemas from
    local disk files rather than from remote locations.  It can also provide
    map schema URIs to arbitrary URL locations.  

    This class can be used (indirectly) as a JSON Schema URI handler to a 
    jsonschema.RefResolver instance; see SchemaHandler.
    """

    def __init__(self, urilocs={}):
        """
        initialize the handler

        :argument dict urilocs:  a dictionary mapping URIs to local file paths
                                 that define the schema identified by the URI.
        """
        self._map = dict(urilocs)

        # the following are used to support SchemaHandler; may be removed if 
        # SchemaHandler is not required for RefResolver
        self._schemes = set()
        self._addschemes(urilocs)

    @classmethod
    def from_directory(cls, dirpath, ensure_locfile=False, 
                       locfile=SCHEMA_LOCATION_FILE):
        """
        create a schemaLoader for schemas stored as files under a given 
        directory.  This factory method will attempt to load schema file 
        names from a file called locfile (defaults to "schemaLocation.json").
        If the file is not found, all the JSON files under that directory
        (including subdirectories) will be examined and those recognized as 
        JSON schemas will be loaded.  
        """
        if not os.path.exists(dirpath):
            raise IOError((errno.ENOENT, "directory not found", dirpath)) 
        if not os.path.isdir(dirpath):
            raise RuntimeError(dirpath + ": not a directory")

        out = SchemaLoader()

        locpath = os.path.join(dirpath, locfile)
        if os.path.exists(locpath):
            out.load_locations(locpath, dirpath)
        else:
            dc = DirectorySchemaCache(dirpath)
            out.add_locations(dc.locations())
            if ensure_locfile:
                dc.save_locations(locfile)

        return out

    @classmethod
    def from_location_file(cls, locpath, basedir=None):
        """
        create a schemaLoader for schemas listed in a schema location file.

        :argument str basedir:  the base directory that document paths are 
                                assumed to be relative to.  If not given, any
                                relative paths will be assumed to be relative
                                to the directory containing the location file. 
        """
        out = SchemaLoader()
        out.load_locations(locpath, basedir)
        return out

    def _addschemes(self, map):
        # used to support SchemaHandler
        for loc in self._map:
            self._schemes.add(urlparse(loc).scheme)

    def locate(self, uri):
        """
        return the file path location of the schema for the given URI or None
        if the schema is not known to be available locally.

        :exc `KeyError` if the location of the schema has not been set
        """
        return self._map[uri]

    def iterURIs(self):
        """
        return an iterator for the uris mapped in this instance
        """
        return self._map.iterkeys()

    def __len__(self):
        return len(self._map)

    def add_location(self, uri, path):
        """
        set the location of the schema file corresponding to the given URI
        """
        self._map[uri] = path
        self._schemes.add(urlparse(uri).scheme)

    def add_locations(self, urifiles):
        """
        add all the URI-file mappings in the given dictionary
        """
        self._map.update(urifiles)
        self._addschemes(urifiles)

    def load_schema(self, uri):
        """
        return the parsed json schema document for a given URI.

        :exc `KeyError` if the location of the schema has not been set
        :exc `IOError` if an error occurs while trying to read from the 
                       registered location.  This includes if the file is
                       not found or reading causes a syntax error.  
        """
        loc = self.locate(uri)
        url = urlparse(loc)

        # Note: this part adapted from jsonschema.RefResolver.resolve_remote()
        # (v2.5.1)
        if not url.scheme:
            with open(loc) as fd:
                return json.load(fd)
        elif (
            scheme in [u"http", u"https"] and
            requests and
            getattr(requests.Response, "json", None) is not None
        ):
            # Requests has support for detecting the correct encoding of
            # json over http
            if callable(requests.Response.json):
                result = requests.get(loc).json()
            else:
                result = requests.get(loc).json
        else: 
            # Otherwise, pass off to urllib and assume utf-8
            result = json.loads(urlopen(uri).read().decode("utf-8"))

        return result

    def load_locations(self, filename, basedir=None):
        """
        load in a mapping of URIs to file paths from a file.  This uses the
        location module to read the mappings file.  

        :argument str filename:  a file path to the mappings file.  The format 
                                 should be any of the formats supported by this 
                                 class.
        """
        self.add_locations(read_loc_file(filename, basedir=basedir))

class SchemaHandler(Mapping):
    """
    A wrapper class to use a SchemaLoader as a JSON Schema URI handler to a 
    jsonschema.RefResolver instance.  
    """

    def __init__(self, loader, strict=False):
        """
        initialize the handler

        :argument dict urilocs:  a dictionary mapping URIs to local file paths
                                 that define the schema identified by the URI.
        """
        self._loader = loader
        self._strict = strict
            
    def __getitem__(self, scheme):
        if self._strict and scheme not in self._loader._schemes:
            raise KeyError(scheme)
        return self._loader

    def __len__(self):
        return len(self._loader._schemes)

    def __iter__(self):
        return self._loader._schemes.__iter__()


class DirectorySchemaCache(object):
    """
    a front end for a cache of schemas stored in files within a single 
    directory.  This class can either pre-load all schemas into memory or 
    simply create a mapping of URIs to file locations.  

    A schema is recognized as a JSON file containing a "$schema" property set 
    to a recognized JSON-Schema URI.  It should also contain an "id" property 
    that contains the schema's URI; if it doesn't, a file-scheme URI will be 
    given to it based on its location on disk.  
    """

    class NotASchemaError(Exception):

        def __init__(self, why=None, filepath=None):
            self.filename = None
            self.path = filepath
            self.why = why

        @property
        def path(self):
            """
            the file path to file containing the non-schema
            """
            return self._path
        @path.setter
        def path(self, val):
            self._path = val
            if val:
                self.filename = os.path.basename(val)
        @path.deleter
        def path(self):
            del self._path

        def __str__(self):
            out = ""
            if self.filename:
                out += self.filename + ": "
            out += "Not a JSON Schema document"
            if why:
                out += ": " + why
            return out

    def __init__(self, dirpath):
        self._dir = dirpath
        self._checkdir()

    def _checkdir(self):
        if not os.path.exists(self._dir):
            raise IOError((errno.ENOENT, "directory not found", self._dir)) 
        if not os.path.isdir(self._dir):
            raise RuntimeError(self._dir + ": not a directory")

    def _read_id(self, fd):
        schema = json.load(fd)
        if not hasattr(schema, "get") or not hasattr(schema,"__getitem__"):
            raise self.NotASchemaError("Does not contain a JSON object")
        try:
            sid = schema["$schema"]
            if sid not in jsch.validators.meta_schemas:
                raise self.NotASchemaError("Unrecognized JSON-Schema $schema")
        except KeyError:
            raise self.NotASchemaError("JSON object does not contain a $schema property")

        return (schema.get("id"), schema)

    def open_file(self, filename):
        """
        read the file in the cache directory with the given filename and 
        return 2-tuple of the schema's id and the parsed schema
        """
        filepath = os.path.join(self._dir, filename)
        with open(filepath) as fd:
            try:
                (id, schema) = self._read_id(fd)
            except self.NotASchemaError, ex:
                ex.path = filename
                raise

            if not id:
                id = "file://" + filepath

            return (id, schema)

    def _iterfiles(self, recurse=True):
        for dir, dirnames, filenames in os.walk(self._dir):
            dir = dir[len(self._dir)+1:]
            for file in map(lambda p: os.path.join(dir, p), 
                            filter(lambda f: f.endswith(".json"), filenames)):
                try:
                    (id, schema) = self.open_file(file)
                    yield file, id, schema
                except self.NotASchemaError, ex:
                    continue
            if not recurse:
                break

    def locations(self, absolute=False, recursive=True):
        """
        return a dictionary that maps schema URIs to their file paths.  

        :argument bool absolute:  if True, the paths returned will be absolute;
                                  by default (False), paths relative to the 
                                  directory are returned. 
        :argument bool recursive: if True (default), this list will include
                                  schemas from subdirectories
        """
        out = {}
        for file, id, schema in self._iterfiles(recursive):
            if absolute:
                file = os.path.join(self._dir, file)
            out[id] = file

        return out

    def schemas(self, recursive=True):
        """
        return a dictionary of mappings of URIs to parsed schemas

        :argument bool recursive: if True (default), this list will include
                                  schemas from subdirectories
        """
        out = {}
        for file, id, schema in self._iterfiles(recursive):
            out[id] = schema

        return out

    def save_locations(self, outfile=SCHEMA_LOCATION_FILE, 
                       absolute=False, recursive=True):
        """
        write the id-location map to a file (in JSON format).  

        :argument str outfile:  the name of the output file.  If not provided,
                     it will be written to a file called "schemaLocation.json"
                     in the cache directory.  A relative path will be 
                     interpreted as relative to the cache directory.  To write
                     to an arbitrary location, one must provide an absolute
                     path.
        :argument bool absolute:  if True, the paths returned will be absolute;
                                  by default (False), paths relative to the 
                                  directory are returned. 
        :argument bool recursive: if True (default), this list will include
                                  schemas from subdirectories
        """
        outfile = os.path.join(self._dir, outfile)

        locs = self.locations(absolute, recursive)

        with open(outfile, "w") as fd:
            json.dump(locs, fd, separators=(",", ": "), indent=4)
