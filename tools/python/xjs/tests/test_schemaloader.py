# import pytest
from __future__ import with_statement
import json, os, pytest
from cStringIO import StringIO
import xjs.schemaloader as loader

locs = {
  "uri:nist.gov/goober": "http://www.ivoa.net/xml/goober",
  "http://mgi.nist.gov/goof": "goof.xml"
}
schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                            os.path.dirname(os.path.dirname(__file__))))), 
                         'schemas','json')
schemafile = os.path.join(schemadir, 'mgi-json-schema.json')

class TestSchemaLoader(object):

    def test_ctor(self):
        ldr = loader.SchemaLoader()
        assert len(set(ldr.iterURIs())) == 0

        ldr = loader.SchemaLoader(locs)
        uris = set(ldr.iterURIs())
        assert len(uris) == 2
        assert "uri:nist.gov/goober" in uris
        assert "http://mgi.nist.gov/goof" in uris

    def test_locate(self):
        ldr = loader.SchemaLoader(locs)
        assert ldr.locate("uri:nist.gov/goober") == \
            "http://www.ivoa.net/xml/goober"
        assert ldr.locate("http://mgi.nist.gov/goof") == "goof.xml"
        assert ldr.locate("ivo://ivoa.net/rofr") is None

    def test_add(self):
        ldr = loader.SchemaLoader()
        assert len(set(ldr.iterURIs())) == 0

        ldr.add_locations(locs)
        uris = set(ldr.iterURIs())
        assert len(uris) == 2
        assert ldr.locate("uri:nist.gov/goober") == \
            "http://www.ivoa.net/xml/goober"
        assert ldr.locate("http://mgi.nist.gov/goof") == "goof.xml"

        ldr = loader.SchemaLoader()
        ldr.add_location("uri:nist.gov/goober", "goober.json")
        assert len(set(ldr.iterURIs())) == 1
        assert ldr.locate("uri:nist.gov/goober") == "goober.json"
        ldr.add_location("http://mgi.nist.gov/goof", 
                         "http://www.ivoa.net/xml/goober")
        assert len(set(ldr.iterURIs())) == 2
        assert ldr.locate("http://mgi.nist.gov/goof") == \
            "http://www.ivoa.net/xml/goober"

    def test_load_schema(self):
        ldr = loader.SchemaLoader()
        ldr.add_location("uri:nist.gov/goober", schemafile)

        schema = ldr.load_schema("uri:nist.gov/goober")
        assert schema
        assert "$schema" in schema
        assert "id" in schema

    def test_call(self):
        ldr = loader.SchemaLoader()
        ldr.add_location("uri:nist.gov/goober", schemafile)

        schema = ldr("uri:nist.gov/goober")
        assert schema
        assert "$schema" in schema
        assert "id" in schema

class TestSchemaHandler(object):

    def test_ctor(self):
        ldr = loader.SchemaHandler(loader.SchemaLoader())
        assert not ldr._strict

        ldr = loader.SchemaHandler(loader.SchemaLoader(locs))
        assert not ldr._strict

        ldr = loader.SchemaHandler(locs, True)
        assert ldr._strict

        ldr = loader.SchemaHandler(loader.SchemaLoader(locs), strict=False)
        assert not ldr._strict

    def test_compat(self):
        ldr = loader.SchemaLoader(locs)
        ldr.add_location("http://mgi.nist.gov/mgi-json-schema/v0.1", 
                         schemafile)
        hdlr = loader.SchemaHandler(ldr)

        assert "uri" in hdlr
        assert "http" in hdlr
        assert len(hdlr) == 2

        assert hdlr["uri"] is ldr
        assert hdlr["http"] is ldr
        assert hdlr["https"] is ldr  # not strict

        schema = hdlr["http"]("http://mgi.nist.gov/mgi-json-schema/v0.1")
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "id" in schema
        assert schema["id"] == "http://mgi.nist.gov/mgi-json-schema/v0.1"

    def test_strict(self):
        ldr = loader.SchemaLoader(locs)
        hdlr = loader.SchemaHandler(ldr, strict=True)
        assert hdlr["uri"] is ldr
        assert hdlr["http"] is ldr

        with pytest.raises(KeyError):
            assert hdlr["https"] is ldr 


        
