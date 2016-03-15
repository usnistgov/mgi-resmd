def subject: { "name": "subject",
               "content": {
                   "children": ["\(.)"],
                   "attrs": [ ]
               }
             };

def element: "<\(.name)> \(.content.children[0]) </\(.name)>";
def subjects: .content.subject | map(subject) | map(element);

subjects | join("\n")


