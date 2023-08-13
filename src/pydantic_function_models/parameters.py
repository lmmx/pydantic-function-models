from inspect import _ParameterKind
from typing import Any, Collection, Literal, Mapping, Union

from pydantic import BaseModel, RootModel, field_validator

__all__ = ["Parameter", "Signature"]


class ReservedParameterName(RootModel):
    root: Literal["v__args", "v__kwargs", "v__positional_only", "v__duplicate_kwargs"]


ParameterName = Union[ReservedParameterName, str]


class Parameter(BaseModel):
    name: ParameterName
    annotation: Any  # | inspect.Parameter._empty
    default: Any  # | inspect.Parameter._empty
    kind: _ParameterKind

    @field_validator("name", mode="after")
    @classmethod
    def reserved_names(cls, name: ParameterName):
        match name:
            case ReservedParameterName():
                raise ValueError(f"{name} argument to ValidatedFunction not permitted")
        return name


class Signature(BaseModel):
    parameters: list[Parameter]

    @field_validator("parameters", mode="before")
    @classmethod
    def listify(cls, parameters: Mapping) -> Collection:
        return parameters.values()


# class _ParameterKind(IntEnum):
#     POSITIONAL_ONLY = 0
#     POSITIONAL_OR_KEYWORD = 1
#     VAR_POSITIONAL = 2
#     KEYWORD_ONLY = 3
#     VAR_KEYWORD = 4
