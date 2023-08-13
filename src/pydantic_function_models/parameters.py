from inspect import _ParameterKind as Kind
from typing import Any, Collection, Literal, Mapping, Union

from pydantic import BaseModel, RootModel, field_validator

__all__ = ["Parameter", "Signature"]


class ReservedParameterName(RootModel):
    root: Literal["v__args", "v__kwargs", "v__positional_only", "v__duplicate_kwargs"]


ParameterName = Union[ReservedParameterName, str]


class ParameterMetadata(BaseModel):
    index: int = -1


class Parameter(BaseModel):
    _meta: ParameterMetadata = ParameterMetadata()
    name: ParameterName
    annotation: Any  # | inspect.Parameter._empty
    default: Any  # | inspect.Parameter._empty
    kind: Kind

    @field_validator("name", mode="after")
    @classmethod
    def reserved_names(cls, name: ParameterName):
        match name:
            case ReservedParameterName():
                raise ValueError(f"{name} argument to ValidatedFunction not permitted")
        return name

    @property
    def is_positional(self) -> bool:
        return self.kind in [Kind.POSITIONAL_ONLY, Kind.POSITIONAL_OR_KEYWORD]

    @property
    def takes_arg(self) -> bool:
        return self.kind == Kind.VAR_POSITIONAL

    @property
    def takes_kwarg(self) -> bool:
        return self.kind == Kind.VAR_KEYWORD


class Signature(BaseModel):
    parameters: list[Parameter]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_args()

    @field_validator("parameters", mode="before")
    @classmethod
    def listify(cls, parameters: Mapping) -> Collection:
        return parameters.values()

    @field_validator("parameters", mode="after")
    @classmethod
    def add_index(cls, parameters: list[Parameter]) -> list[Parameter]:
        for i, p in enumerate(parameters):
            p._meta.index = i
        return parameters

    @property
    def arg_mapping(self) -> dict[int, str]:
        return {p._meta.index: p.name for p in self.parameters if p.is_positional}

    @property
    def takes_args(self) -> bool:
        return any(p.takes_arg for p in self.parameters)

    @property
    def takes_kwargs(self) -> bool:
        return any(p.takes_kwarg for p in self.parameters)


# class _ParameterKind(IntEnum):
#     POSITIONAL_ONLY = 0
#     POSITIONAL_OR_KEYWORD = 1
#     VAR_POSITIONAL = 2
#     KEYWORD_ONLY = 3
#     VAR_KEYWORD = 4
