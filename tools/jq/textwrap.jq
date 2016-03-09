def context: {
    "max_line_width": (($config|.textwrap.max_line_width) // 78)|tonumber,
    "min_line_width": (($config|.textwrap.min_line_width) // 30)|tonumber
};

# return true if the input is a string
def isstring: [strings or null, false][0];

def _break(width): 
    .[0:width] as $line |
    ($line| [match("\\s+";"g")] | [.[-1].offset, .[-1].length]) as $brk |
    [ .[0:($brk|.[0])], .[(($brk|.[0])+($brk|.[1])):length] ];

def _wrap_last(width): .[0:-1] + (.[-1]|_break(width));

def _wrap(width): 
    if (.[-1]|length) > width then _wrap_last(width)|_wrap(width) else . end;

# Break a string into an array of strings that are no longer than a
# given width.  The string is broken at the location of one or more
# spaces; the spaces at the break location are removed.
#
# @arg width integer:   the maximun length of a line in number of characters
#
def wrap(width): 
    if (isstring|not) then error("filter wrap must take a string as input") 
       else . end |
    [.] | _wrap(width) | map(sub("^\\s+";"")|sub("\\s+$";""));

# Convert a string into a newline-delimited string of lines in which each line
# is no bigger than a given width.
#
# @arg width  integer:   the maximum width of a line in number of characters;
#                          The default is given by the config parameter 
#                          textwrap.min_line_width.
# @arg indent integer:   the number of spaces to insert that the beginning of 
#                          each line.  The length of each line will not exceed
#                          width unless text after the inserted space is 
#                          smaller than minwidth.  The default is 0.
# @arg minwidth integer: the minimum width in number of characters of the pre-
#                          indented text for each line.  The default is given 
#                          by the config parameter textwrap.min_line_width.
#
def fill(width; indent; minwidth): 
    if (isstring|not) then error("filter fill must take a string as input") 
       else . end |
    (width-indent) as $usewidth | 
    (if ($usewidth < minwidth) then minwidth else $usewidth end) as $usewidth |
    gsub("\\n"; " ") |
    wrap($usewidth) | map((" "*indent)+.) | join("\n");
def fill(width; indent): context as $context |
    fill(width; indent; ($context|.min_line_width));
def fill(width): context as $context |
    fill(width; 0; ($context|.min_line_width));
def fill: context as $context |
    fill(($context|.max_line_width); 0; ($context|.min_line_width));

