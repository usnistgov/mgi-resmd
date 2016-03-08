def subject: "<subject> \(.) </subject>";

def subjects: map(subject) | join("\n");

.content.subject | subjects