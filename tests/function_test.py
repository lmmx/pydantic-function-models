from pydantic import ValidationError
from pytest import mark, raises

from pydantic_function_models.validated_function import ValidatedFunction

from .helpers.data import add_json_schema
from .helpers.funcdefs import add, reserved_params


@mark.parametrize("expected", [add_json_schema])
def test_validated_function(expected):
    f = ValidatedFunction(add)
    assert f.model
    assert f.model.model_json_schema() == expected
    t = type(f.model)
    assert str(t.__module__) == "pydantic._internal._model_construction"
    assert str(t.__name__) == "ModelMetaclass"
    assert f.p_models


def test_invalid_signature():
    with raises(ValidationError):
        ValidatedFunction(reserved_params)
