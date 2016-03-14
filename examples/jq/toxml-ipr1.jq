import "xml" as xml;

def subjects: .subject | xml::textarray2elements("subject");

def Content: xml::element_content([]
    + [xml::text_element("type"; .type)]
    + (.description |  xml::textarray2elements("description"))
    + subjects
    + [xml::text_element("referenceURL"; .referenceURL)]
    + (.referenceCitation | xml::textarray2elements("referenceCitation"))
    + (.primaryAudience | xml::textarray2elements("primaryAudience"))
);

def Identity: xml::element_content([]
    + [xml::text_element("title"; .title)]
    + [xml::text_element_if("shortName"; .shortName)]
    + [xml::text_element_if("version"; .version)]
    + (.identifier | xml::textarray2elements("identifier"))
    + [xml::text_element_if("logo"; .logo)]
);

def Curation: xml::element_content([]
    + [xml::text_element("publisher"; .publisher)]
);

def Resource: xml::element_content([]
    + [.identity|xml::element("identity"; Identity)]
    + [.content|xml::element("content"; Content)];
    
    [xml::attribute("xmlns";""), xml::attribute("xsi:type"; "rsm:Resource"),
     xml::attribute("xmlns:rms"; "urn:nist.gov/schema/res-md/1.0wd"),
     xml::attribute("xmlns:ms"; "urn:nist.gov/schema/mat-sci_res-md/1.0wd")]);

def resource: xml::element("Resource"; Resource) | xml::add_xsidef2element;

def content: xml::element("content"; Content);

. | resource | xml::print({"value_pad": 1})

#.content | content | xml::print({"value_pad": 1})
#.content | [subjects]
