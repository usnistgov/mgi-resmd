# mgi-resmd

a repository for the development of resource metadata schemas and
related tools in support for the Materials Genome Initiative at NIST.

## Dependencies

The tools component of this package, including the xjs python library,
has the following dependencies:

   * python 2.7.x  (python 3.x not yet supported)
   * jsonschema 2.5.x or later
   * jsonspec 0.9.16 or later
   * requests

In addition, the testing framework uses py.test. 

## Running Tests

The included tests apply unit-tests to the tool code and scripts.
Tests also check the correctness of the schemas and examples.  

Currently, tests only exist for the JSON schemas, examples, and
tools.  py.test is used to execute these tests.   To run, change into
the root directory of this distribution and type "py.test".  

## Disclaimer

This repository serves as a platform for open community collaboration
to enable and encourage greater sharing of and interoperability
between research data from around the world.  Except where otherwise
noted, the content and software within this repository should be
considered a work in progress, may contain input from non-governmental
contributors, and thus should not be construed to represent the
position nor have the endorsement the United States government.  

The content and software contained in this repository is provided "AS
IS" with no warrenty of any kind.  


