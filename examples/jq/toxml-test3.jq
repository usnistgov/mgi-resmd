import "xml" as xml;

def subject: xml::element("subject") + xml::element_content(.);
def subjects: .subject | map(subject);
def content: xml::element("content") + xml::element_content(subjects);

.content | content
