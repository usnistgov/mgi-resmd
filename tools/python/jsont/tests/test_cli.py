import pytest, os, sys, json, argparse
from cStringIO import StringIO

from jsont import cli

def test_opts():

    parser = cli.define_opts("jsont")
    opts = parser.parse_args("-Dgoob=gurn -Dfoo=bar ss.json".split())
    assert len(opts.context) == 2
    assert opts.context[0] == "goob=gurn"
    assert opts.context[1] == "foo=bar"

def test_required_args():

    parser = cli.define_opts("jsont")
    with pytest.raises(SystemExit):
        opts = parser.parse_args("-Dgoob=gurn -Dfoo=bar".split())

def test_parse():

    context = {}
    context.update(cli._parse_ctx_args("goob=gurn blah= foo=bar param=1=2".split()))
    assert context["goob"] == "gurn"
    assert context["foo"] == "bar"
    assert context["blah"] == ""
    assert context["param"] == "1=2"
    assert len(context) == 4

def test_bad_parse():

    with pytest.raises(ValueError):
        context = {}
        context.update(cli._parse_ctx_args("goob=gurn =hank foo=bar".split()))

    with pytest.raises(ValueError):
        context = {}
        context.update(cli._parse_ctx_args("goob=gurn hank foo=bar".split()))

class TstSys(object):
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.exc_info = sys.exc_info
        self.argv = [ "tstsys" ]
        self.exitcode = -1

    def exit(self, code):
        self.exitcode = code
        
@pytest.fixture
def tstsys():
    out = TstSys()
    argparse._sys = out
    def finalize():
        argparse._sys = sys

    return out

exdirname = "jstrans"
exdir = os.path.join(os.path.dirname(
   os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                        "examples", exdirname)


def test_basic(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = map(lambda f: os.path.join(exdir, f), 
                          "testtemplate4.json testdoc4.json".split())
    #pytest.set_trace()
    ecode = app.execute()

    result = json.loads(tstsys.stdout.getvalue())
    assert isinstance(result, dict)
    assert result['contacts'][0].keys()[0] == "Bob"
    assert result['contacts'][0]["Bob"] == "Bob <bob@gmail.com>"

    assert tstsys.stdout.getvalue()[-1] == '\n'

    lines = tstsys.stdout.getvalue().split('\n')
    assert len(lines) == 2

    assert ecode == 0

def test_pretty(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = ["-p"]
    tstsys.argv.extend( map(lambda f: os.path.join(exdir, f), 
                            "testtemplate4.json testdoc4.json".split()) )
    #pytest.set_trace()
    ecode = app.execute()

    result = json.loads(tstsys.stdout.getvalue())
    assert isinstance(result, dict)
    assert result['contacts'][0].keys()[0] == "Bob"
    assert result['contacts'][0]["Bob"] == "Bob <bob@gmail.com>"

    lines = tstsys.stdout.getvalue().split('\n')
    assert len(lines) == 8

    line = filter(lambda l: "contacts" in l, lines)[0]
    assert line.startswith('    "')

    assert ecode == 0

def test_indent(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = ["-Djson.indent=2"]
    tstsys.argv.extend( map(lambda f: os.path.join(exdir, f), 
                            "testtemplate4.json testdoc4.json".split()) )
    #pytest.set_trace()
    ecode = app.execute()

    result = json.loads(tstsys.stdout.getvalue())
    assert isinstance(result, dict)
    assert result['contacts'][0].keys()[0] == "Bob"
    assert result['contacts'][0]["Bob"] == "Bob <bob@gmail.com>"

    lines = tstsys.stdout.getvalue().split('\n')
    assert len(lines) == 8

    line = filter(lambda l: "contacts" in l, lines)[0]
    assert line.startswith('  "')

    assert ecode == 0

def test_param(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = "-Djson.indent=2 -Djson.dict_separator=:=".split()
    tstsys.argv.extend( map(lambda f: os.path.join(exdir, f), 
                            "testtemplate4.json testdoc4.json".split()) )
    #pytest.set_trace()
    ecode = app.execute()

    lines = tstsys.stdout.getvalue().split('\n')
    assert len(lines) == 8

    line = filter(lambda l: "contacts" in l, lines)[0]
    assert line.startswith('  "')
    assert '"contacts":=[' in line

    assert ecode == 0

def test_missing_ss(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = "-Djson.indent=2 -Djson.dict_separator=:=".split()

    #pytest.set_trace()
    ecode = app.execute()

    assert ecode == 10
    assert "usage: " in tstsys.stderr.getvalue()

def test_no_force_json(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = map(lambda f: os.path.join(exdir, f), 
                          "testtemplate1.json testdoc4.json".split())
    #pytest.set_trace()
    ecode = app.execute()

    assert tstsys.stdout.getvalue() == \
        "a substitution token looks like this: {texpr}\n"

def test_force_json(tstsys):

    app = cli.JSONT("goob", tstsys.stdout, tstsys.stderr)
    tstsys.argv[1:] = ["-j"]
    tstsys.argv.extend( map(lambda f: os.path.join(exdir, f), 
                            "testtemplate1.json testdoc4.json".split()) )
    #pytest.set_trace()
    ecode = app.execute()

    assert tstsys.stdout.getvalue() == \
        '"a substitution token looks like this: {texpr}"\n'
    assert json.loads(tstsys.stdout.getvalue()) == \
        "a substitution token looks like this: {texpr}"



