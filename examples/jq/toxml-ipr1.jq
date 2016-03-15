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

def RelevantDate: (keys | .[0]) as $role | 
    xml::element_content([ .[$role] ]; [$role | xml::attribute("role")]);

def dates: .date//[] | map(RelevantDate | xml::element("date"));

def Contact: xml::element_content([]
    + [.name | idable_text_element("name")]
    + [.postalAddress | xml::text_element("postalAddress")]
    + [.emailAddress  | xml::text_element("emailAddress")]
    + [.phoneNumber   | xml::text_element("phoneNumber")]
    + [.timeZone      | xml::text_element("timeZone")]
);
#def contacts: .contact | map(Contact | xml::element("contact"));
def contacts: .contact | select(.) | Contact | [xml::element("contact")];

def Curation: xml::element_content([]
    + [.publisher | idable_text_element("publisher")]
    + (.creator//[] | map(idable_text_element("creator")))
    + (.contributor//[] | map(idable_text_element("contributor")))
    + dates
    + contacts
);

def Applicability: xml::element_content([]
    + (.materialType  | map(xml::text_element("materialType")))
    + (.propertyClass | map(xml::text_element("propertyClass")))
    ; [] 
    + [ .["$extensionSchemas"] | .[0] | xml::attribute("xsi:type") ]
);

def Policy: xml::element_content([] 
    + (.rights//[] | map(xml::text_element("rights")))
    + [.terms | xml::text_element("terms")]
);

def Portal: xml::element_content([]
    + [.description | xml::text_element("description")]
    + [.title | xml::text_element("title")]
    + [.homeURL | xml::text_element("homeURL")]
);

def Access: xml::element_content([]
    + [.policy | Policy | xml::element("policy")]
    + (.portal | map(Portal | xml::element("portal")) )
#    + [.serviceAPI | ServiceAPI | xml::element("serviceAPI")]
#    + [.download | Download | xml::element("download")]
);

def Resource: xml::element_content([]
    + [.identity | Identity | xml::element("identity")]
    + [.curation | Curation | xml::element("curation")]
    + [.content | Content | xml::element("content")]
    + (.applicability | map(Applicability | xml::element("applicability")))
    + [.access | Access | xml::element("access")]
    ;
    
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
