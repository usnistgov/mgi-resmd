import "xml" as xml;

def subjects: .subject | xml::textarray2elements("subject");

def IdentifierInfo:
    (strings | [xml::attribute("pid")]),
    (objects | [.id | xml::attribute("pid"), .scheme |xml::attribute("scheme")]);

def NameID:
    (strings | xml::element_content([.])),
    (arrays  | xml::element_content([.[0]]; .[1] | IdentifierInfo));
                             

def idable_text_element(name):
    NameID | xml::element(name);

def refcits: .referenceCitation | (arrays//[]) |
    map(idable_text_element("referenceCitation"));

def Content: xml::element_content([]
    + [(.type//"") | xml::text_element("type")]
    + (.description |  xml::textarray2elements("description"))
    + subjects
    + [(.referenceURL/"") | xml::text_element("referenceURL")]
    + refcits
    + (.primaryAudience | xml::textarray2elements("primaryAudience"))
);

def Identity: xml::element_content([]
    + [(.title//"") | xml::text_element("title")]
    + [.shortName | xml::text_element("shortName")]
    + [.version | xml::text_element("version")]
    + (.identifier | xml::textarray2elements("identifier"))
    + [.logo | xml::text_element("logo")]
);

def Curation: xml::element_content([]
    + [.publisher | idable_text_element("publisher")]
    + (.creator//[] | map(idable_text_element("creator")))
);

def Resource: xml::element_content([]
    + [.identity | Identity | xml::element("identity")]
    + [.curation | Curation | xml::element("curation")]
    + [.content | Content | xml::element("content")];
    
    [(""|xml::attribute("xmlns")),
     ("rsm:Resource" | xml::attribute("xsi:type")),
     ("urn:nist.gov/schema/res-md/1.0wd" | xml::attribute("xmlns:rms")),
     ("urn:nist.gov/schema/mat-sci_res-md/1.0wd" | xml::attribute("xmlns:ms"))])
;

def resource: Resource | xml::element("Resource") | xml::add_xsidef2element;

def content: Content | xml::element("content");

. | resource | xml::print({"value_pad": 1})

#.content | content | xml::print({"value_pad": 1})
#.content | [subjects]
