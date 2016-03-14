import "xml" as xml;

def textarray2elements(name):
    map(xml::element(name; xml::element_content(.)));
def subjects: .subject | textarray2elements("subject");

def Content: xml::element_content([]
    + [xml::text_element("type"; .type)]
    + (.description |  textarray2elements("description"))
    + subjects
    + [xml::text_element("referenceURL"; .referenceURL)]
    + (.referenceCitation | textarray2elements("referenceCitation"))
    + (.primaryAudience | textarray2elements("primaryAudience"))
);

def Resource: xml::element_content([]
    + [.content|xml::element("content"; Content)];
    [xml::attribute("xmlns";""), xml::attribute("xsi:type"; "rsm:Resource"),
     xml::attribute("xmlns:rms"; "urn:nist.gov/schema/res-md/1.0wd"),
     xml::attribute("xmlns:ms"; "urn:nist.gov/schema/mat-sci_res-md/1.0wd")]);

def resource: xml::element("Resource"; Resource) | xml::add_xsidef2element;

def content: xml::element("content"; Content);

. | resource | xml::print({"value_pad": 1})

#.content | content | xml::print({"value_pad": 1})
#.content | [subjects]
