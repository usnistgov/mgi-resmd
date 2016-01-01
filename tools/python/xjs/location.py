"""
a module for determining the location of a JSON schema based on its URI.  
This includes the ability to make use of copies of the schema documents on 
local disk.
"""
from __future__ import with_statement
import sys, os, json
from urlparse import urlparse

def parse_mappings_asjson(fd):
    """
    read the locations contained in the given file stream.  The format
    should be a JSON object whose keys are the URIs and their values the 
    corresponding file paths where the schema for each URI is located. 

    :argument file fd:  the file stream object containing the data in 
                        JSON format
    :return dict: containing the parsed mappings

    :exc `ValueError` if the stream does not contain valid JSON or 
                      otherwise contains data that cannot be coverted to
                      a dictionary.
    """
    return json.load(fd)

def parse_mappings_astxt(fd):
    """
    read the locations contained in the given file stream.  The expected
    format is simple plain-text in which each line contains a single 
    mapping, where the first space-delimited word is the URI and the second 
    is the location.  Lines that start with # will be ignored.  

    :argument file fd:  the file stream object containing the data in 
                        text format

    :exc `ValueError` if a non-empty, non-comment record in the file does 
                      not contain at least 2 space delimited words.
    """
    out = {}
    for line in fd:
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue

        uri, loc = line.split()[0:2]
        out[uri] = loc

    return out

_parsers = { "json": parse_mappings_asjson,
             "txt": parse_mappings_astxt    }

def register_location_file_parser(ext, parser):
    """
    register a location file parser to handle files with a given filename 
    extension.

    :argument str ext:  the file extension to register the parser with.  The 
                        string should not contain a dot (.).  Files ending 
                        with this extension will be parsed with the given 
                        parser.
    :argument func parser:  a function to invoke as a parser for files of 
                        the given extension.  
    """
    _parsers.set(ext, func)

class LocationReader(object):
    """
    a class that will read locations for documents from files.  
    """

    def __init__(self, basedir=None, parsers=_parsers):
        """
        initialize the reader

        :argument str basedir:  the base directory that document paths are 
                                assumed to be relative to.  If not given, any
                                relative paths will be assumed to be relative
                                to the directory containing the location file. 
        :argument parsers:  a dictionary of parser functions that should be 
                            invoked based on the file extension.  
        """
        self.parsers = parsers
        self.basedir = basedir
        self.deffmt = 'txt'

    def read(self, locfile, fmt=None, basedir=None):
        """
        read a given location file and load the URI-location mappings into
        the given dictionary.

        :argument str locfile:  the path to the location file to read.  
                                Relative file paths will be relative to the 
                                current working directory.
        :argument str fmt:      the format of the file to assume as identified
                                by a registered filename extension (e.g. "json",
                                "txt").  
        :argument str basedir:  the basedir to assume for relative file path
                                locations found in the file; this overrides the
                                basedir set at construction time.  

        :exc `ValueError` if the file contents does not comply with the 
                          expected format.
        """
        if basedir is None:
            basedir = self.basedir
        if basedir is None:
            basedir = os.path.abspath(os.path.dirname(locfile))

        if not fmt:
            fmt = os.path.splitext(locfile)[1][1:]
        if not fmt:
            fmt = self.deffmt

        # find an appropriate parser
        u2l = self.parsers.get(fmt)
        if not u2l:
            if not fmt:
                raise RuntimeError("No default parser set to apply to "+
                                   locfile)
            raise RuntimeError("Don't know how to parse location file of " +
                               "type '" + fmt + "'")

        # parse the file
        with open(locfile) as fd:
            out =u2l(fd)

        # turn simple file URIs into paths; turn relative paths into 
        # absolute ones
        for uri, loc in out.iteritems():
            locurl = urlparse(loc, scheme='file')
            if locurl.scheme == 'file' and not locurl.netloc:
                loc = locurl.path
                if basedir:
                    loc = os.path.abspath(os.path.join(basedir, loc))
                out[uri] = loc

        return out

def read_loc_file(locfile, fmt=None, basedir=None):
    """
    read a given location file and load the URI-location mappings into
    the given dictionary.

    :argument str locfile:  the path to the location file to read.  
                            Relative file paths will be relative to the 
                            current working directory.
    :argument str fmt:      the format of the file to assume as identified
                            by a registered filename extension (e.g. "json",
                            "txt").  
    :argument str basedir:  the base directory that document paths are 
                            assumed to be relative to.  If not given, any
                            relative paths will be assumed to be relative
                            to the directory containing the location file. 

    :exc `ValueError` if the file contents does not comply with the 
                      expected format.
    """
    return LocationReader(basedir).read(locfile, fmt)

