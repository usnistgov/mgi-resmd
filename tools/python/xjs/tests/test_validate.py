# import pytest
from __future__ import with_statement
import json, os, pytest
from cStringIO import StringIO
import xjs.validate as validate

locs = {
  "uri:nist.gov/goober": "http://www.ivoa.net/xml/goober",
  "http://mgi.nist.gov/goof": "goof.xml"
}
schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                            os.path.dirname(os.path.dirname(__file__))))), 
                         'schemas','json')
schemafile = os.path.join(schemadir, 'mgi-json-schema.json')

class TestAltLocationSchemaLoader(object):

    def test_ctor(self):
        ldr = validate.AltLocationSchemaLoader()
        assert len(set(ldr.iterURIs())) == 0

        ldr = validate.AltLocationSchemaLoader(locs)
        uris = set(ldr.iterURIs())
        assert len(uris) == 2
        assert "uri:nist.gov/goober" in uris
        assert "http://mgi.nist.gov/goof" in uris

    def test_locate(self):
        ldr = validate.AltLocationSchemaLoader(locs)
        assert ldr.locate("uri:nist.gov/goober") == \
            "http://www.ivoa.net/xml/goober"
        assert ldr.locate("http://mgi.nist.gov/goof") == "goof.xml"
        assert ldr.locate("ivo://ivoa.net/rofr") is None

    def test_add(self):
        ldr = validate.AltLocationSchemaLoader()
        assert len(set(ldr.iterURIs())) == 0

        ldr.add_locations(locs)
        uris = set(ldr.iterURIs())
        assert len(uris) == 2
        assert ldr.locate("uri:nist.gov/goober") == \
            "http://www.ivoa.net/xml/goober"
        assert ldr.locate("http://mgi.nist.gov/goof") == "goof.xml"

        ldr = validate.AltLocationSchemaLoader()
        ldr.add_location("uri:nist.gov/goober", "goober.json")
        assert len(set(ldr.iterURIs())) == 1
        assert ldr.locate("uri:nist.gov/goober") == "goober.json"
        ldr.add_location("http://mgi.nist.gov/goof", 
                         "http://www.ivoa.net/xml/goober")
        assert len(set(ldr.iterURIs())) == 2
        assert ldr.locate("http://mgi.nist.gov/goof") == \
            "http://www.ivoa.net/xml/goober"

    def test_load_schema(self):
        ldr = validate.AltLocationSchemaLoader()
        ldr.add_location("uri:nist.gov/goober", schemafile)

        schema = ldr.load_schema("uri:nist.gov/goober")
        assert schema
        assert "$schema" in schema
        assert "id" in schema

    def test_call(self):
        ldr = validate.AltLocationSchemaLoader()
        ldr.add_location("uri:nist.gov/goober", schemafile)

        schema = ldr("uri:nist.gov/goober")
        assert schema
        assert "$schema" in schema
        assert "id" in schema

class TestAltLocationSchemaHandler(object):

    def test_ctor(self):
        ldr = validate.AltLocationSchemaHandler()
        assert len(set(ldr.iterURIs())) == 0

        ldr = validate.AltLocationSchemaHandler(locs)
        uris = set(ldr.iterURIs())
        assert len(uris) == 2
        assert "uri:nist.gov/goober" in uris
        assert "http://mgi.nist.gov/goof" in uris

        ldr = validate.AltLocationSchemaHandler(locs, True)
        assert len(set(ldr.iterURIs())) == 2
        assert ldr._strict

        ldr = validate.AltLocationSchemaHandler(locs, strict=False)
        assert len(set(ldr.iterURIs())) == 2
        assert not ldr._strict

    def test_call(self):
        ldr = validate.AltLocationSchemaHandler()
        ldr.add_location("uri:nist.gov/goober", schemafile)

        schema = ldr("uri:nist.gov/goober")
        assert schema
        assert "$schema" in schema
        assert "id" in schema

    def test_compat(self):
        ldr = validate.AltLocationSchemaHandler(locs)
        ldr.add_location("http://mgi.nist.gov/mgi-json-schema/v0.1", schemafile)

        assert "uri" in ldr
        assert "http" in ldr
        assert len(ldr) == 2

        assert ldr["uri"] is ldr
        assert ldr["http"] is ldr
        assert ldr["https"] is ldr  # not strict

        schema = ldr["http"]("http://mgi.nist.gov/mgi-json-schema/v0.1")
        assert isinstance(schema, dict)
        assert "$schema" in ldr
        assert "id" in ldr
        assert schema["id"] == "http://mgi.nist.gov/mgi-json-schema/v0.1"

    def test_strict(self):
        ldr = validate.AltLocationSchemaHandler(locs, strict=True)
        assert ldr["uri"] is ldr
        assert ldr["http"] is ldr

        with pytest.raises(KeyError):
            assert ldr["https"] is ldr 


        
