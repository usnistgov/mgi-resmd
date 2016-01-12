import os, pytest

input = { "goob": "gurn" }
context = { "foo": "bar" }

from xjs.trans.exceptions import *

def test_JSONTransformException():
    try:
        raise JSONTransformException("Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None

    try:
        raise JSONTransformException("Oops", RuntimeError("dangit"))
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"

def test_TransformConfigException():
    try:
        raise TransformConfigException("Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.transform is None

    try:
        raise TransformConfigException("Oops", "$lb", RuntimeError("dangit"))
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.transform == "$lb"

def test_TransformNotFound():
    try:
        raise TransformNotFound("toxml", "Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.transform == "toxml"

    try:
        raise TransformNotFound("toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Named transform could not be found: toxml"
        assert ex.cause is None
        assert ex.transform == "toxml"

def test_TransformConfigParamError():
    try:
        raise TransformConfigParamError("pretty", "toxml", "Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.transform == "toxml"
        assert ex.param == "pretty"

    try:
        raise TransformConfigParamError("pretty", "toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "toxml transform config error: problem with pretty parameter"
        assert ex.cause is None
        assert ex.transform == "toxml"
        assert ex.param == "pretty"


def test_MissingTransformData():
    try:
        raise MissingTransformData(message="Oops")
        pytest.fail("failed to raise")
    except MissingTransformData, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.param is None
        assert ex.transform is None

    try:
        raise MissingTransformData("delim")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "transform config error: missing parameter: delim"
        assert ex.cause is None
        assert ex.param == "delim"
        assert ex.transform is None

    try:
        raise MissingTransformData("t", "json")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "json transform config error: missing parameter: t"
        assert ex.cause is None
        assert ex.param == "t"
        assert ex.transform == "json"

    try:
        raise MissingTransformData("t", "json", "Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.param == "t"
        assert ex.transform == "json"

def test_TransformConfigTypeError():
    try:
        raise TransformConfigTypeError("pretty", "bool", "str", "toxml", "Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.transform == "toxml"
        assert ex.param == "pretty"
        assert ex.typeneeded == 'bool'
        assert ex.typegot == 'str'

    try:
        raise TransformConfigTypeError("pretty", "bool", "str", "toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "toxml transform: Invalid type for pretty parameter: need bool, got str."
        assert ex.cause is None
        assert ex.transform == "toxml"
        assert ex.param == "pretty"
        assert ex.typeneeded == 'bool'
        assert ex.typegot == 'str'

def TestStringTemplateSyntaxError():

    try:
        raise TestStringTemplateSyntaxError("Missing end brace")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Syntax error in string template: Missing end brace"
        assert ex.cause is None
        assert ex.transform is None
        assert ex.template is None

    try:
        raise TestStringTemplateSyntaxError("Missing end brace", "unescape {",
                                            "toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message.startswith("Syntax error in string template (toxml): Missing end brace: 'unescaped {'")
        assert ex.cause is None
        assert ex.transform == "toxml"
        assert ex.template == "unescape {"

def test_TransformApplicationException():
    try:
        raise TransformApplicationException("Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise TransformApplicationException("Oops", input, context)
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.input is input
        assert ex.context is context
        assert ex.transform is None

    try:
        raise TransformApplicationException("Oops", input, context, "toxml", 
                                            RuntimeError("dangit"))
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.input is input
        assert ex.context is context
        assert ex.transform == "toxml"

    try:
        raise TransformApplicationException.due_to(RuntimeError("dangit"),
                                                   input, context, "toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Failed to apply toxml transform: RuntimeError('dangit',)"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.input is input
        assert ex.context is context
        assert ex.transform == "toxml"

    try:
        raise TransformApplicationException.due_to(RuntimeError("dangit"),
                                                   input, context, "toxml", 
                                                   "forgot")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "forgot: RuntimeError('dangit',)"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.input is input
        assert ex.context is context
        assert ex.transform == "toxml"

def test_DataExtractionError():
    try:
        raise DataExtractionError("Oops")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise DataExtractionError("Oops", input, context)
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is None
        assert ex.input is input
        assert ex.context is context
        assert ex.transform is None

    try:
        raise DataExtractionError("Oops", input, context, "toxml", 
                                            RuntimeError("dangit"))
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "Oops"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.input is input
        assert ex.context is context
        assert ex.transform == "toxml"

    try:
        raise DataExtractionError.due_to(RuntimeError("dangit"),
                                         input, context, "toxml")
        pytest.fail("failed to raise")
    except JSONTransformException, ex:
        assert ex.message == "toxml transform: problem extracting data: RuntimeError('dangit',)"
        assert ex.cause is not None
        assert isinstance(ex.cause, Exception)
        assert str(ex.cause) == "dangit"
        assert ex.input is input
        assert ex.context is context
        assert ex.transform == "toxml"

