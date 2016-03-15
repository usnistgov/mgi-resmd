import "xml" as xml;

def subject: xml::text_element("subject");
def subjects: .subject | map(subject);
def content: xml::element_content(subjects) | xml::element("content");

.content | content | xml::print
