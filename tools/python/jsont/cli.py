"""
Command-line front end into tranformations
"""
import os, sys, errno, json, re, traceback
from argparse import ArgumentParser

from .engine import DocEngine
from .exceptions import *

description = \
"""transform a JSON document against a stylesheet"""

epilog = None

def define_opts(progname):

    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('ssheet', metavar='STYLE', type=str,
                        help="the input JSON document to transform")
    parser.add_argument('doc', metavar='DOC', type=str, nargs='?',
                        help="the input JSON document to transform")
    parser.add_argument('-p', '--pretty-print', action='store_true', 
                        dest='pretty',
                        help="insert spaces and newlines to make the JSON "+
                             "output pretteier")
    parser.add_argument('-j', '--json-out', action='store_true',dest='forcejson',
                        help="Force JSON output, even when the result is text")
    parser.add_argument('-D', type=str, dest='context', action='append', 
                        help="set context paramter")
    parser.add_argument('-S', type=str, dest='system', action='append', 
                        help="set system paramter")
    parser.add_argument('-q', '--quiet', action='store_true', 
                        help="suppress messages explaining why documents are "
                            +"invalid; only short success/failure message for "
                            +"each file is printed.")
    parser.add_argument('-s', '--silent', action='store_true', 
                        help="suppress all output; the exit code indicates "
                            +"if any of the files are invalid.")

    return parser

class Runner(object):

    def __init__(self, progname=None, optsfunc=None, out=sys.stdout, 
                 err=sys.stderr, qopt='quiet', sopt='silent'):
        self._parser = optsfunc(progname)
        self.opts = None
        self._q = qopt
        self._s = sopt
        self.err = err
        self.out = out

    @property
    def prog(self):
        return self._parser.prog

    def execute(self, args=None):
        """
        execute the script by parsing the command line arguments and calling
        the run() method.

        :return int:  the code to exit with
        """
        self.opts = self._parser.parse_args(args)
        try:
            return self.run()
        except Exception, ex:
            tb = sys.exc_info()[2]
            origin = traceback.extract_tb(tb)[-1]
            return self.fail(UNEXPECTED, "Unexpected exception at {0}, line {1}: {2}".format(origin[0], origin[1], repr(ex)))

    def run(self):
        return 0

    def fail(self, exitcode, message):
        """
        print a failure message and return the given exit code
        """
        self.complain(message)
        return exitcode

    def complain(self, message):
        if (hasattr(self.opts, self._q) and getattr(self.opts, self._q)) or \
           (hasattr(self.opts, self._q) and getattr(self.opts, self._q)):
            return

        if self.prog:
            self.err.write(self.prog)
            self.err.write(": ")
        self.err.write(message)
        self.err.write('\n')
        self.err.flush()

    def advise(self, message):
        if hasattr(self.opts, self._q) and getattr(self.opts, self._q):
            return

        self.err.write(message)
        self.err.write('\n')
        self.err.flush()

    def tell(self, message):
        if hasattr(self.opts, self._s) and getattr(self.opts, self._s):
            return

        self.out.write(message)
        self.out.write('\n')
        self.out.flush()

FILENOTFOUND = 1
INVALID_PARAM = 3
BADJSON_SS = 4
BADJSON_DOC = 5
INVALIDTRANS = 6
TRANSFORMERROR = 7

UNEXPECTED = 10

class JSONT(Runner):
    def __init__(self, progname=None, out=sys.stdout, err=sys.stderr):
        Runner.__init__(self, progname, define_opts, out, err)

    def run(self):
        """
        execute the jsont script.  

        Command line arguments are parsed from sys.argv.  
        """

        context = { }
        if self.opts.pretty:
            context['json.indent'] = 4
        if self.opts.context:
            try:
                context.update(_parse_ctx_args(self.opts.context))
            except ValueError, ex:
                return self.fail(INVALID_PARAM, "bad parameter syntax: "+str(ex))
        if 'json.indent' in context and context['json.indent'] is not None:
            if not isinstance(context['json.indent'], int):
                try:
                    context['json.indent'] = int(context['json.indent'])
                except ValueError, ex:
                    return self.fail(INVALID_PARAM, 
                                     "json.indent: bad parameter type: "+
                                     context['json.indent'])

        system = { }
        if self.opts.system:
            try:
                context.update(_parse_ctx_args(self.opts.system))
            except ValueError, ex:
                return self.fail(INVALID_PARAM, "bad parameter syntax: "+str(ex))

        if not os.path.exists(self.opts.ssheet):
            return self.fail(FILENOTFOUND, self.opts.ssheet + ": file not found")
        if self.opts.doc and not os.path.exists(self.opts.doc):
            return self.fail(FILENOTFOUND, self.opts.doc + ": file not found")

        # load the stylesheet file
        try:
            with open(self.opts.ssheet) as fd:
                ss = json.load(fd)
        except ValueError, ex:
            return self.fail(BADJSON_SS, 
                             "JSON syntax error in stylesheet: " + str(ex))

        try:
            eng = DocEngine(ss, context, system)
        except TransformConfigException, ex:
            return self.fail(INVALIDTRANS, "Stylesheet configuration error: " +
                             str(ex))

        # read the input document
        try:
            if self.opts.doc:
                with open(self.opts.doc) as fd:
                    doc = json.load(fd)
            else:
                doc = json.load(sys.stdin)
        except ValueError, ex:
            return self.fail(BADJSON_DOC, 
                             "JSON syntax error in input document: " + str(ex))

        try:
            if not self.opts.silent:
                eng.write(self.out, doc, self.opts.forcejson)
            else:
                eng.transform(doc)
        except TransformApplicationException, ex:
            return self.fail(TRANSFORMERROR, "Transformation failed: " + str(ex))

        return 0


def _parse_ctx_args(ctxargs):
    spltr = re.compile(r'\s*=\s*')
    for arg in ctxargs:
        if not spltr.search(arg):
            raise ValueError("missing '=' delimiter")
        (key, val) = spltr.split(arg, 1)
        if not key:
            raise ValueError("empty parammeter name")
        yield (key, val)
