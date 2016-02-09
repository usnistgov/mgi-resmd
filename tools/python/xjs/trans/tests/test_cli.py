import pytest

from xjs.trans import cli

def test_opts():

    parser = cli.define_opts("jsont")
    opts = parser.parse_args("-Dgoob=gurn -Dfoo=bar doc.json ss.json".split())
    assert len(opts.context) == 2
    assert opts.context[0] == "goob=gurn"
    assert opts.context[1] == "foo=bar"


