import os, pytest

input = { "goob": "gurn" }
context = { "foo": "bar" }

from xjs.trans.exceptions import *

def test_TransformException():
    try:
        raise TransformException("Oops")
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Oops"
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise TransformException("Oops", "t", input, context)
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Oops"
        assert ex.transform == "t"
        assert ex.input['goob'] == 'gurn'
        assert ex.context['foo'] == 'bar'


def test_TransformStateException():
    try:
        raise TransformException("Oops")
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Oops"
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise TransformException("Oops", "t", input, context)
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Oops"
        assert ex.transform == "t"
        assert ex.input['goob'] == 'gurn'
        assert ex.context['foo'] == 'bar'


def test_TransformStateException():
    try:
        raise TransformStateException()
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Unknown internal failure"
        assert ex.cause is None
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise TransformStateException(KeyError("boob"))
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert isinstance(ex.cause, KeyError)
        assert ex.message.startswith("Internal transform failure: KeyError(")
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise TransformStateException(KeyError("boob"), "Oops", "t", 
                                      input, context)
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert isinstance(ex.cause, KeyError)
        assert ex.message == "Oops"
        assert ex.transform == "t"
        assert ex.input['goob'] == 'gurn'
        assert ex.context['foo'] == 'bar'


def test_MissingTransformData():
    try:
        raise MissingTransformData(message="Oops")
        pytest.fail("failed to raise")
    except MissingTransformData, ex:
        assert ex.message == "Oops"
        assert ex.param is None
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise MissingTransformData("delim")
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "transform invalid: missing parameter: delim"
        assert ex.param == "delim"
        assert ex.transform is None
        assert ex.input is None
        assert ex.context is None

    try:
        raise MissingTransformData("t", "json")
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "json transform invalid: missing parameter: t"
        assert ex.param == "t"
        assert ex.transform == "json"

    try:
        raise MissingTransformData("t", "json", "Oops")
        pytest.fail("failed to raise")
    except TransformException, ex:
        assert ex.message == "Oops"
        assert ex.param == "t"
        assert ex.transform == "json"

