from inspect import _ParameterKind
from typing import Any, Collection, Mapping

from pydantic import BaseModel, field_validator

__all__ = ["Parameter", "Signature"]

# class _ParameterKind(IntEnum):
#     POSITIONAL_ONLY = 0
#     POSITIONAL_OR_KEYWORD = 1
#     VAR_POSITIONAL = 2
#     KEYWORD_ONLY = 3
#     VAR_KEYWORD = 4


class Parameter(BaseModel):
    name: str
    annotation: Any  # | inspect.Parameter._empty
    default: Any  # | inspect.Parameter._empty
    kind: _ParameterKind


class Signature(BaseModel):
    parameters: list[Parameter]

    @field_validator("parameters", mode="before")
    @classmethod
    def listify(cls, mapping: Mapping) -> Collection:
        return mapping.values()
