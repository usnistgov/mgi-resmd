import os, pytest, types

import jsont.transforms.xml as xml
from xjs.validate import ExtValidator
from jsont.engine import StdEngine
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

    
