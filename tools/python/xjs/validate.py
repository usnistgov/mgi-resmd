"""
a module that provides support for validating schemas that support 
extended json-schema tags.
"""
from __future__ import with_statement
import sys, os, json
import jsonschema
import jsonschema as jsch
from jsonschema.exceptions import ValidationError, SchemaError
from collections import Mapping

class ExtValidator(object):
    """
    A validator that can validate an instance against multiple schemas
    """

    def __init__(self, schemaLoader=None):
        """
        initialize the validator for a set of expected schemas
        """
        self._loader = schemaLoader
        self._handler = SchemaHandler(schemaLoader)
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
        loader.SchemaLoader.from_directory(dirpath)

    def validate(self, instance, minimally=False, strict=False):
        """
        validate the instance document against its schema and its extensions
        as directed.  
        """
        baseSchema = instance.get("$schema")
        if not baseSchema:
            raise ValidationError("Base schema ($schema) not specified; " +
                                  "unable to validate")

        self.validate_against(instance, baseSchema, True)

        if not minimally:
            inst = Instance(instance)
            extensions = dict(inst.find_extend_objs())
            for uri in extensions:
                self.validate_against(instance, extensions[uri], strict)
            

    def validate_against(self, instance, schemauris=[], strict=False):
        """
        validate the instance against each of the schemas identified by the 
        list of schemauris.  For the instance to be considered valid, it 
        must validate against each of the named schemas.

        :argument instance:  a parsed JSON document to be validated.
        :argument list schemauris:  a list of URIs of the schemas to validate
                                    against.  
        :argument bool strict:  if True, validation will fail if any of the 
                                schema URIs cannot be resolved to a schema.
                                if False, unresolvable schemas URIs will be 
                                ignored and validation against that schema will
                                be skipped.  
        """
        if isinstance(schemauris, str):
            schemauris = [ schemauris ]
        schema = None
        out = True
        for uri in schemauris:
            val = self._validators.get(uri)
            if not val:
                schema = self._schemaStore[uri]
                if not schema:
                    try:
                        schema = self._loader(uri)
                    except KeyError, e:
                        if strict:
                            raise SchemaError("Unable to resolve schema for " + 
                                              uri)
                        continue
                resolver = jsch.RefResolver(uri, schema, self._schemaStore,
                                            self._handler)

                cls = jsch.validator_for(schema)
                cls.check_schema(schema)
                val = cls(schema, resolver=resolver)

            try:
                val.validate(instance)
            finally:
                self._schemaStore.update(val.resolver.store)

