"""
The implementation for the script that provides the command-line interface (CLI)
"""
import os, sys, errno, json
from argparse import ArgumentParser
from ..validate import ExtValidator, ValidationError, SchemaError
from ..schemaloader import SchemaLoader

description = \
"""validate one or more JSON documents against their schemas"""

epilog=None

def define_opts(progname=None):

    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('files', metavar='FILE', type=str, nargs='+',
                        help="files to validate")
    parser.add_argument('-S', '--doc-schema', type=str, dest='docschema',
                        metavar='URI', 
                        help="the URI of the schema to assume for the document"
                            +"as a whole (overriding the internal id)")
    parser.add_argument('-L', '--schema-location', type=str, dest='loc',
                        metavar='DIR_OR_FILE', default=None,
                        help="Either a directory containing cached schemas "
                             +"or a schema location file")
    parser.add_argument('-g', '--ignore-extensions', action='store_true',
                        dest='minimal', 
                        help="Ignore any extension declarations when "
                            +"validating")
    parser.add_argument('-C', '--strict', action='store_true',
                        dest='strict', 
                        help="Fail if an extensions schema cannot be loaded "
                            +"(otherwise, ignore unresolvable extensions)")
    parser.add_argument('-q', '--quiet', action='store_true', 
                        help="suppress messages explaining why documents are "
                            +"invalid; only short success/failure message for "
                            +"each file is printed.")
    parser.add_argument('-s', '--silent', action='store_true', 
                        help="suppress all output; the exit code indicates "
                            +"if any of the files are invalid.")

    return parser

# Exit codes
INVALID   = 1    # one or more input files are invalid
BADSCHEMA = 2    # problem found with one or more schemas (including missing)
BADINPUTS = 3    # bad inputs provided (including files not found)

UNEXPECTED = 10

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
            return self.fail(UNEXPECTED, "Unexpected exception: " + str(ex))

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

    

class Validate(Runner):
    def __init__(self, progname=None, out=sys.stdout, err=sys.stderr):
        Runner.__init__(self, progname, define_opts, out, err)

    def run(self):
        """
        execute the validate script.  

        Command line arguments are parsed from sys.argv.  
        """
        loader = None

        if self.opts.loc:
            if not os.path.exists(self.opts.loc):
                return fail(BADINPUTS, 
                            self.opts.loc + ": schema file/dir not found")

            if os.path.isdir(self.opts.loc):
                loader = SchemaLoader.from_directory(self.opts.loc)
            else:
                loader = SchemaLoader.from_location_file(self.opts.loc)


        val = ExtValidator(loader)

        doc = None
        anyinvalid = False
        badschema = False
        for filename in self.opts.files:
            try:
                if not os.path.exists(filename):
                    self.complain(filename + ": file not found.")
                    continue
                with open(filename) as fd:
                    doc = json.load(fd)

                val.validate(doc, self.opts.minimal, self.opts.strict, 
                             self.opts.docschema)

                if not self.opts.silent:
                    self.tell("{0}: valid!".format(os.path.basename(filename)))
            except (ValidationError, SchemaError), ex:
                f = os.path.basename(filename)
                self.advise("{0}:".format(f))
                self.advise(str(ex))
                self.tell("{0}: not valid.".format(f))
                anyinvalid = True
                if isinstance(ex, SchemaError):
                    badschema = True


        return (badschema and BADSCHEMA) or (anyinvalid and INVALID) or 0
