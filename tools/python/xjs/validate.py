"""
a module that provides support for validating schemas that support 
extended json-schema tags.
"""
from __future__ import with_statement
import sys, os, types, json, urlparse
import jsonschema
import jsonschema.validators as jsch
from jsonschema.exceptions import (ValidationError, SchemaError, 
                                   RefResolutionError)

from . import schemaloader as loader
from .instance import Instance, EXTSCHEMAS

# These are URIs that identify versions of the JSON Enhanced Schema schem
EXTSCHEMA_URIS = [ "http://mgi.nist.gov/mgi-json-schema/v0.1" ]

class ExtValidator(object):
    """
    A validator that can validate an instance against multiple schemas
    """

    def __init__(self, schemaLoader=None):
        """
        initialize the validator for a set of expected schemas
        """
        if not schemaLoader:
            schemaLoader = loader.SchemaLoader()
        self._loader = schemaLoader
        self._handler = loader.SchemaHandler(schemaLoader)
        self._schemaStore = {}
        self._validators = {}

    @classmethod
    def with_schema_dir(self, dirpath):
        """
        Create an ExtValidator that leverages schema cached as files in a 
        directory.  

        Before creating the ExtValidator, this factory will establish use
        of the cache: first, it will look for a file in that directory called 
        schemaLocation.json to identify the available schemas.  If that file
        does not exist, all JSON files in that directory will examined to find
        JSON schemas.  From this list of schemas, a SchemaLoader instance will 
        be passed into the ExtValidator constructor.

        See the location module for more information about schema location 
        files.  See schemaloader.SchemaLoader for more information about 
        creating loaders for schema files on disk.  
        """
        return ExtValidator(loader.SchemaLoader.from_directory(dirpath))

    def load_schema(self, schema, uri=None):
        """
        load a pre-parsed schema into the validator.  The schema will be checked 
        for errors first and raise an exception if there is a problem.  If schema
        with the given ID was already loaded, it will get overriden.  

        :argument dict schema:  the parsed schema object.
        :argument str  uri:     The URI to associated with the schema.  If not 
                                 provided, the value of the "id" property will
                                 be used.  
        """
        if not uri:
            uri = schema.get('id')
        if not uri:
            raise ValueError("No id property found; set uri param instead.")

        # check the schema
        vcls = jsch.validator_for(schema)
        vcls.check_schema(schema)

        # now add it
        self._schemaStore[uri] = schema
        
        
    def validate(self, instance, minimally=False, strict=False, schemauri=None):
        """
        validate the instance document against its schema and its extensions
        as directed.  
        """
        baseSchema = schemauri
        if not baseSchema:
            baseSchema = instance.get("$schema")
        if not baseSchema:
            raise ValidationError("Base schema ($schema) not specified; " +
                                  "unable to validate")

        self.validate_against(instance, baseSchema, True)

        if not minimally:
            # we need to validate any portions including the EXTSCHEMAS property
            inst = Instance(instance)
            extensions = dict(inst.find_extended_objs())

            # If instance is actually an extension schema schema, we need to
            # ignore the definition of the EXTSCHEMAS property.
            is_extschema = self.is_extschema_schema(instance)
            
            for ptr in extensions:
                # make sure that the EXTSCHEMAS property is invoked properly
                if not isinstance(extensions[ptr][EXTSCHEMAS], list):
                    if not is_extschema or \
                       not isinstance(extensions[ptr][EXTSCHEMAS], dict):
                        msg = "invalid value type for {0} (not an array):\n     {1}"\
                              .format(EXTSCHEMAS, extensions[ptr][EXTSCHEMAS])
                        raise ValidationError(msg)
                    else:
                        # this is the extension schema schema, so ignore this
                        # node
                        continue
                
                for val in extensions[ptr][EXTSCHEMAS]:
                    if not isinstance(val, types.StringTypes):
                        raise ValidationError(
                            "invalid {0} array item type:\n    {1}"
                            .format(EXTSCHEMAS, val))
                    
                # now validate marked portion
                self.validate_against(extensions[ptr], 
                                      extensions[ptr][EXTSCHEMAS], strict)
            

    def validate_against(self, instance, schemauris=[], strict=False):
        """
        validate the instance against each of the schemas identified by the 
        list of schemauris.  For the instance to be considered valid, it 
        must validate against each of the named schemas.  $extensionSchema
        properties within the instance are ignored.  

        :argument instance:  a parsed JSON document to be validated.
        :argument list schemauris:  a list of URIs of the schemas to validate
                                    against.  
        :argument bool strict:  if True, validation will fail if any of the 
                                schema URIs cannot be resolved to a schema.
                                if False, unresolvable schemas URIs will be 
                                ignored and validation against that schema will
                                be skipped.  
        """
        if isinstance(schemauris, str) or isinstance(schemauris, unicode):
            schemauris = [ schemauris ]
        schema = None
        out = True
        for uri in schemauris:
            val = self._validators.get(uri)
            if not val:
                (urib,frag) = self._spliturifrag(uri)
                schema = self._schemaStore.get(urib)
                if not schema:
                    try:
                        schema = self._loader(urib)
                    except KeyError, e:
                        if strict:
                            raise SchemaError("Unable to resolve schema for " + 
                                              urib)
                        continue
                resolver = jsch.RefResolver(uri, schema, self._schemaStore,
                                            handlers=self._handler)

                if frag:
                    try:
                        schema = resolver.resolve_fragment(schema, frag)
                    except RefResolutionError, ex:
                        raise SchemaError("Unable to resolve fragment, "+frag+
                                          "from schema, "+ urib)

                cls = jsch.validator_for(schema)
                cls.check_schema(schema)
                val = cls(schema, resolver=resolver)

            try:
                val.validate(instance)
            finally:
                self._validators[uri] = val
                self._schemaStore.update(val.resolver.store)

    def _spliturifrag(self, uri):
        parts = urlparse.urldefrag(uri)
        if not parts[1] and uri.endswith('#'):
            return (uri, '')
        return parts

    def validate_file(self, filepath, minimally=False, strict=False):
        """
        open the specified file and validated its contents.  This is 
        equivalent to loading the JSON in the file and passing it to 
        validate().
        """
        with open(filepath) as fd:
            instance = json.load(fd)
        self.validate(instance, minimally, strict)

    def is_extschema_schema(self, instance):
        """
        return true if the given JSON instance has both an "id" property
        set to one of the recognized URIs for a version of the JSON Enhanced 
        Schema (Supporting Extensions) _and_ an "$extensionSchema" property.
        """
        return instance.get('id') in EXTSCHEMA_URIS and \
               instance.has_key(EXTSCHEMAS)
