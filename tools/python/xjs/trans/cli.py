"""
Command-line front end into tranformations
"""
import os, sys, errno, json
from argparse import ArgumentParser

description = \
"""transform a JSON document against a stylesheet"""

epilog = None

def define_opts(progname):

    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('ssheet', metavar='STYLE', type=str,
                        help="the input JSON document to transform")
    parser.add_argument('doc', metavar='DOC', type=str, 
                        help="the input JSON document to transform")
    parser.add_argument('-p', '--pretty-print', action='store_true', 
                        dest='pretty',
                        help="insert spaces and newlines to make the JSON "+
                             "output pretteier")
    parser.add_argument('-D', type=str, dest='context', action='append', 
                        help="set context paramter")

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
            return self.fail(UNEXPECTED, "Unexpected exception: " + repr(ex))

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

    

class JSONT(Runner):
    def __init__(self, progname=None, out=sys.stdout, err=sys.stderr):
        Runner.__init__(self, progname, define_opts, out, err)

    def run(self):
        """
        execute the jsont script.  

        Command line arguments are parsed from sys.argv.  
        """

        pass



