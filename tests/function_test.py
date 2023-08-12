from pytest import mark

from pydantic_function_models.validated_function import (
    ValidatedFunction,
    validate_arguments,
)

from .helpers.data import add_json_schema
from .helpers.funcdefs import add

# def test_ai_extract(target, expected, fake_page, mocker):


@mark.parametrize("expected", [add_json_schema])
def test_validate_arguments(expected):
    f = validate_arguments(add)
    assert f.model
    assert f.model.model_json_schema() == expected


@mark.parametrize("expected", [add_json_schema])
def test_validated_function(expected):
    f = ValidatedFunction(add)
    assert f.model
    assert f.model.model_json_schema() == expected
