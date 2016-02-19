"""
Various functions for parsing strings and transform directives.
"""
import re
from .exceptions import TransformConfigException

FUNC_PAT = re.compile(r'^([\w\.]+)\((.*)\)$')

class ConfigSyntaxError(TransformConfigException):
    """
    an exception indicating a syntax error was detected while the parsing 
    a directive within a configuration string.  
    """

    def __init__(self, message, cause=None):
        super(ConfigSyntaxError, self).__init__(message, cause=cause)

class FunctionSyntaxError(ConfigSyntaxError):
    """
    an exception indicating a syntax error was detected while the parsing a 
    function invocation.  
    """

    def __init__(self, message, cause=None):
        super(FunctionSyntaxError, self).__init__(message, cause)

def chomp_quote(instr):
    """
    split the input string into a quoted string (with either " or ') and 
    everything after it.  To split, the input string must have 
    a quote character as its first non-whitespace character.  The returned 
    quoted string will include its quotes but it will be stripped of extra 
    surrounding space.  The remaining text will not be stripped.  
    """
    qc = instr[0]
    if qc not in "\"'":
        return '', instr
    bcc = 0
    i = 1

    while i < len(instr):
        if instr[i] == qc:
            if bcc % 2 == 0:
                break
            bcc = 0
        elif instr[i] == '\\':
            bcc += 1
        i += 1
    
    if i >= len(instr):
        raise ConfigSyntaxError("Missing closing quote ("+qc+"): "+instr)
    return instr[:i+1], instr[i+1:]

def chomp_br_enclosure(argstr):
    """
    split the input string into a string enclosed in braces or brackets and 
    everything after it.  To split, the input string must have a brace or a
    bracket character as its first non-whitespace character.  The returned 
    eclosed string will include its enclosing characters but it will be 
    stripped of extra surrounding space.  The remaining text will not be 
    stripped.  
    """
    out = None
    start = argstr[0]
    end = start
    lev = 1

    if start == '{':
        end = '}'
    elif start == '[':
        end = ']'
    else:
        return '', argstr

    i = 1;
    while lev > 0 and i < len(argstr):
        if argstr[i] == start:
            lev += 1
        elif argstr[i] == end:
            lev -= 1
        elif argstr[i] in "\"'":
            quote, rest = chomp_quote(argstr[i:])
            i += len(quote)-1
        i += 1

    if lev > 0:
        raise ConfigSyntaxError("Expected '" + end + 
                                "' to end enclosure: " + argstr)
    if i >= len(argstr):
        return argstr, ''

    return argstr[:i], argstr[i:]

def chomp_arg(argstr):
    """
    assume the input string is a function argument list and split it into the 
    first argument and everything else.  The argument ends at the first comma
    that isn't surrounded by quotes, braces, or brackets.  
    """
    if argstr[0] in "{[":
        tok, rest = chomp_br_enclosure(argstr)
    elif argstr[0] in "\"'":
        tok, rest = chomp_quote(argstr)
    else:
        parts = re.split(r'(,)', argstr, 1)
        tok = parts[0].strip()
        rest = ''
        if len(parts) > 1:
            rest = ''.join(parts[1:])

    rest = rest.lstrip()
    if len(rest) > 0 and rest[0] != ',':
        raise ConfigSyntaxError("Expected argument delimiter (','): "+rest)
    rest = rest.lstrip(', ')

    return tok, rest

def parse_argstr(argstr):
    """
    split the input string into a list of parsed arguments.  Arguments are 
    delimited by commas that are not enclosed by quotes, braces, or brackets.  
    """
    out = []
    while len(argstr) > 0:
        tok, argstr = chomp_arg(argstr)
        out.append(tok)

    return out

def parse_function(funcstr):
    """
    parse a function invocation into its function name and a list of arguments
    """
    match = FUNC_PAT.search(funcstr)
    if not match:
        raise FunctionSyntaxError("Does not match function syntax, f(...): "+
                                  funcstr)

    tf, argstr = match.group(1,2)
    try:
        args = parse_argstr(argstr)
    except ConfigSyntaxError, ex:
        raise FunctionSyntaxError("Function Syntax Error: " + str(ex), 
                                  cause=ex)
    return tf, args
