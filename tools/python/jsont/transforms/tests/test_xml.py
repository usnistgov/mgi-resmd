import os, pytest, types

import jsont.transforms.xml as xml
from xjs.validate import ExtValidator
from jsont.engine import StdEngine, DocEngine
from jsont.exceptions import *

@pytest.fixture(scope="module")
def engine(request):
    return DocEngine()

xsiuri = "http://www.w3.org/2001/XMLSchema-instance"
msuri  = "urn:nist.gov/schema/mat-sci_res-md/1.0wd"

def test_determine_prefix():

    prefixes = { xsiuri: "xsi",
                 msuri: "ms",
                 "uri:goob": "ns12" }

    ns = "urn:nist.gov/schema/res-md/1.0wd"
    pre = "rsm"
    xmlns = ''
    assert pre not in prefixes

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(ns, pre, {}, pfs)

    assert p == 'rsm:'
    assert 'xmlns:{0}="{1}"'.format(pre, ns) in defs
    assert ns in pfs

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(None, 'ms', {}, pfs)

    assert p == 'ms:'
    assert len(defs) == 0
    assert ns not in pfs

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(ns, None, {}, pfs)

    assert p == 'ns13:'
    assert 'xmlns:ns13="{0}"'.format(ns) in defs
    assert ns in pfs
    assert pfs[ns] == 'ns13'

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(msuri, None, {}, pfs)

    assert p == 'ms:'
    assert len(defs) == 0
    assert msuri in pfs
    assert pfs[msuri] == 'ms'

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(ns, 'br', {'xml.xmlns': ns}, pfs)

    assert p == ''
    assert len(defs) == 0
    assert ns not in pfs

    pfs = dict(prefixes)
    p, defs = xml.determine_prefix(ns, 'br', 
                                   {'xml.xmlns': ns, 'xml.prefer_prefix': True },
                                   pfs)

    assert p == 'br:'
    assert 'xmlns:br="{0}"'.format(ns) in defs
    assert ns in pfs

def test_format_text():

    context = {
        'xml.indent_step': 4,
        'xml.text_packing': 'pretty',
        'xml.indent': 8,
        'xml.min_line_length': 30,
        'xml.max_line_length': 70
    }

    longtext = '"Becker, C.A. et al., "Considerations for choosing and using force fields and interatomic potentials in materials science and engineering," Current Opinion in Solid State and Materials Science, 17, 277-283 (2013).'

    text = xml.format_text(longtext, context)
    lines = text.split('\n')
    assert len(lines) > 1
    assert lines[0] == '        "Becker, C.A. et al., "Considerations for choosing and using'
    assert max(map(lambda l: len(l), lines)) <= 70
    assert max(map(lambda l: len(l), map(lambda n: n.strip(), lines))) <= 62

    ctxt = dict(context)
    ctxt['xml.indent_step'] = -1
    text = xml.format_text(longtext, ctxt)
    lines = text.split('\n')
    assert len(lines) == 1
    assert lines[0].startswith('"Becker, C.A. et al., "Considerations')
    assert len(lines[0]) > 70

    ctxt = dict(context)
    ctxt['xml.text_packing'] = 'loose'
    text = xml.format_text(longtext, ctxt)
    lines = text.split('\n')
    assert len(lines) == 1
    assert lines[0].startswith('        "Becker, C.A. et al., "Considerations')
    assert len(lines[0]) > 70

    ctxt = dict(context)
    ctxt['xml.indent'] = 56
    text = xml.format_text(longtext, ctxt)
    lines = text.split('\n')
    assert len(lines) > 1
    assert min(map(lambda l: len(l), lines)) > 70
    assert max(map(lambda l: len(l), map(lambda n: n.strip(), lines))) <= 30

def test_format_atts():

    context = {
        'xml.indent_step': 4,
        'xml.text_packing': 'pretty',
        'xml.indent': 8,
        'xml.min_line_length': 30,
        'xml.max_line_length': 50
    }

    attrs = [
        { 
            "name": "role",
            "value": "creation",
        },
        {
            "name": "type",
            "value": "vo:Service",
            "namespace": xsiuri
        },
        {
            "name": "id",
            "value": "goober",
            "namespace": "urn:gurn"
        }
    ]

    prefixes = { xsiuri: "xsi",
                 msuri: "ms",
                 "uri:goob": "ns12" }

    fmtd = xml.format_atts(attrs, 10, context, prefixes)
    lines = fmtd.split('\n')
    assert len(lines) == 2
    assert lines[0] == ' role="creation" xsi:type="vo:Service"'
    assert lines[-1].endswith(' xmlns:ns13="urn:gurn"')

    
def test_format_element_simple():

    element = {
        "name": "subject",
        "content": {
            "children": [ "metals" ]
        },
        "hints": {
            "xml.value_pad": 2
        }
    }
    context = {
        "xml.indent": 4,
        "xml.style": 'pretty'
    }
    prefixes = { xsiuri: "xsi",
                 msuri: "ms",
                 "uri:goob": "ns12" }

    text = xml.format_element(element, context, prefixes, "gurn")
    assert text == "    <subject>  metals  </subject>"

    ctx = dict(context)
    ctx['xml.style'] = 'compact'
    text = xml.format_element(element, ctx, prefixes, "gurn")
    assert text == "<subject>metals</subject>"

def test_format_element_wrap():

    longtext = 'Becker, C.A. et al., "Considerations for choosing and using force fields and interatomic potentials in materials science and engineering," Current Opinion in Solid State and Materials Science, 17, 277-283 (2013).'

    element = {
        "name": "referenceCitation",
        "content": {
            "children": [ longtext ],
            "attrs": [
                {
                    "name": "pid",
                    "value": "doi:10.1016/j.cossms.2013.10.001"
                }
            ]
        },
        "hints": {
            "xml.value_pad": 2
        }
    }
    context = {
        "xml.indent": 5,
        "xml.style": 'pretty'
    }
    prefixes = { xsiuri: "xsi",
                 msuri: "ms",
                 "uri:goob": "ns12" }

    formatted = \
"""     <referenceCitation pid="doi:10.1016/j.cossms.2013.10.001">
       Becker, C.A. et al., "Considerations for choosing and using force
       fields and interatomic potentials in materials science and
       engineering," Current Opinion in Solid State and Materials Science, 17,
       277-283 (2013).
     </referenceCitation>"""

    #pytest.set_trace()
    text = xml.format_element(element, context, prefixes, "gurn")
    assert text == formatted


def test_format_text_hier():

    element = {
        "name": "applicability",
        "content": {
            "attrs": [
                {
                    "name": "type",
                    "prefix": "xsi",
                    "namespace": xsiuri,
                    "value": "ms:MaterialsScience"
                },
                'xmlns:ms="'+msuri+'"'
            ],
            "children": [
                {
                    "name": "materialType",
                    "content": {
                        "children": [ "non-specific" ]
                    }
                },
                {
                    "name": "propertyClass",
                    "content": {
                        "children": [ "simulated" ]
                    }
                },
                {
                    "name": "propertyClass",
                    "content": {
                        "children": [ "structural" ]
                    }
                }
            ]
        },
    }

    context = {
        "xml.indent": 0,
        "xml.style": 'pretty',
        "xml.value_pad": 1
    }

    formatted = \
"""<applicability xsi:type="ms:MaterialsScience"
               xmlns:ms="urn:nist.gov/schema/mat-sci_res-md/1.0wd"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <materialType> non-specific </materialType>
  <propertyClass> simulated </propertyClass>
  <propertyClass> structural </propertyClass>
</applicability>"""

    text = xml.format_element(element, context)
    assert text == formatted

class TestToAttribute(object):

    def test_simple_literal(self, engine):
        config = {
            "name": "role",
            "value": "report"
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "report"

    def test_simple_select(self, engine):
        config = {
            "name": "role",
            "value": "{/foo}"
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "bar"

    def test_transf_val1(self, engine):
        config = {
            "name": "role",
            "value": { "$val": "/foo" }
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "bar"

    def test_transf_val2(self, engine):
        config = {
            "name": "role",
            "value": { "$type": "extract", "select": "/foo" }
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "bar"

    def test_transf_val3(self, engine):
        config = {
            "name": "role",
            "value": {"$val": { "$type": "extract", "select": "/foo" }}
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "bar"

    def test_name_select(self, engine):
        config = {
            "name": "{/foo}",
            "value": "{/foo}"
        }

        #pytest.set_trace()
        transf = xml.ToAttribute(config, engine, type="attribute")
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "bar"
        assert at['value'] == "bar"

    def test_asfunc(self, engine):
        config = {
            "$type": "apply",
            "transform": "xml.attribute('role', /foo)"
        }

        #pytest.set_trace()
        transf = engine.make_transform(config)
        at = transf({'foo': 'bar'}, {})

        assert at['name'] == "role"
        assert at['value'] == "bar"

        



class TestToElementContent(object):

    def test_simple_literal(self, engine):
        config = {
            "children": [ "metals" ],
            "attrs": [
                {
                    "$type": "xml.attribute",
                    "name": "role",
                    "value": "report"
                },
                "xml.attribute('xmlns', '')" 
            ]
        }

        transf = xml.ToElementContent(config, engine, type="elementContent")
        el = transf({'foo': 'bar'}, {})

        assert el['children'] == [ "metals" ]
        assert el['attrs' ][0]['name'] == "role"
        assert el['attrs' ][1]['name'] == "xmlns"

    def test_complex_content(self, engine):
        config = {
            "children": [ 
                {
                    "$type": "xml.textElement",
                    "name": "subject",
                    "value": "metals",
                    "hints": { "xml.value_pad": 1 }
                },
                { "$val": "xml.textElement('subject', /foo)" }
            ],
            "attrs": [
                {
                    "$type": "xml.attribute",
                    "name": "role",
                    "value": "report"
                },
                "xml.attribute('xmlns', '')" 
            ]
        }

        transf = xml.ToElementContent(config, engine, type="elementContent")
        el = transf({'foo': 'bar'}, {})

        assert len(el['children']) == 2
        assert isinstance(el['children'][0], dict)
        assert el['children'][0]['name'] == "subject"
        assert isinstance(el['children'][1], dict)
        assert el['children'][1]['name'] == "subject"
        assert el['children'][1]['content']['children'][0] == "bar"
        assert el['attrs' ][0]['name'] == "role"
        assert el['attrs' ][1]['name'] == "xmlns"

class TestToElement(object):

    def test_simple_literal(self, engine):
        config = {
            "name": "subject",
            "content": {
                "children": [ "metals" ],
                "attrs": [
                    {
                        "name": "role",
                        "value": "report"
                    },
                    {
                        "name": "xmlns",
                        "value": ""
                    }
                ]
            },
            "hints": { "xml.value_pad": 1 }
        }

        transf = xml.ToElement(config, engine, type="element")
        el = transf({'foo': 'bar'}, {})

        assert el['name'] == "subject"
        assert el['content']['children'] == [ "metals" ]
        assert el['content']['attrs' ][0]['name'] == "role"
        assert el['content']['attrs' ][1]['name'] == "xmlns"

        out = xml.format_element(el, {})
        assert out == '<subject role="report" xmlns=""> metals </subject>'

class TestToTextElement(object):

    def test_literal(self, engine):
        config = {
            "name": "subject",
            "value": "metals",
            "hints": { "xml.value_pad": 1 }
        }

        transf = xml.ToTextElement(config, engine, type="textElement")
        el = transf({'foo': 'bar'}, {})
        assert el['name'] == "subject"
        assert el['content']['children'] == [ "metals" ]

        out = xml.format_element(el, {})
        assert out == "<subject> metals </subject>"

    
schemadir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))), "schemas", "json")
moddir = os.path.dirname(os.path.dirname(__file__))

@pytest.fixture(scope="module")
def validator(request):
    return ExtValidator.with_schema_dir(schemadir)

def validate(validator, filename):
    validator.validate_file(os.path.join(schemadir, filename), False, True)

def test_ss(validator):
    ss = os.path.join(moddir, "xml_ss.json")
    validate(validator, ss)

def test_transf_schema(validator):
    ss = os.path.join(schemadir, "jsont-xml-transf.json")
    validate(validator, ss)

def test_int_schema(validator):
    ss = os.path.join(schemadir, "jsont-xml-schema.json")
    validate(validator, ss)
