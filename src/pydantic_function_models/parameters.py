from inspect import Parameter as _Parameter
from inspect import _ParameterKind as Kind
from typing import Any, Collection, Dict, List, Literal, Mapping, Tuple, Union

from pydantic import (
    BaseModel,
    RootModel,
    ValidationInfo,
    field_validator,
    model_validator,
)

__all__ = ["Parameter", "Signature"]

ALT_V_ARGS = "v__args"
ALT_V_KWARGS = "v__kwargs"
V_POSITIONAL_ONLY_NAME = "v__positional_only"
V_DUPLICATE_KWARGS = "v__duplicate_kwargs"


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
    empty: Any

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
    def is_positional_or_kw(self) -> bool:
        return self.kind == Kind.POSITIONAL_OR_KEYWORD

    @property
    def is_positional_only(self) -> bool:
        return self.kind == Kind.POSITIONAL_ONLY

    @property
    def is_kw_only(self) -> bool:
        return self.kind == Parameter.KEYWORD_ONLY

    @property
    def is_var_pos(self) -> bool:
        return self.kind == Kind.VAR_POSITIONAL

    @property
    def is_var_kw(self) -> bool:
        return self.kind == Kind.VAR_KEYWORD

    @property
    def takes_arg(self) -> bool:
        return self.kind == Kind.VAR_POSITIONAL

    @property
    def takes_kwarg(self) -> bool:
        return self.kind == Kind.VAR_KEYWORD

    @property
    def is_untyped(self) -> bool:
        return self.annotation is self.empty

    @property
    def has_no_default(self) -> bool:
        return self.default is self.empty


class Signature(BaseModel):
    parameters: list[Parameter]
    type_hints: dict[str, Any] = {}
    fields: dict[str, tuple[Any, Any]] = {}
    v_args_name: str = "args"
    v_kwargs_name: str = "kwargs"

    @model_validator(mode="after")
    @classmethod
    def set_type_hints(cls, values: "Signature", info: ValidationInfo) -> "Signature":
        values.type_hints = info.context
        return values

    @model_validator(mode="after")
    @classmethod
    def set_fields(cls, self: "Signature") -> "Signature":
        self.fields = self.make_fields()
        return self

    def make_fields(self) -> dict[str, tuple[Any, Any]]:
        """
        Make tuples of (annotation, default) for each parameter.
        """
        fields = {
            p.name: (
                (Any if p.is_untyped else self.type_hints[p.name]),
                (... if p.has_no_default else p.default),
            )
            for p in self.parameters
            if (p.is_positional_only or p.is_positional_or_kw or p.is_kw_only)
        }
        for p in self.parameters:
            annotation = Any if p.annotation is p.empty else self.type_hints[p.name]
            if p.is_positional_only:
                fields[V_POSITIONAL_ONLY_NAME] = List[str], None
            elif p.is_positional_or_kw:
                fields[V_DUPLICATE_KWARGS] = List[str], None
            elif p.kind == Parameter.VAR_POSITIONAL:
                # self.v_args_name = name
                fields[p.name] = Tuple[annotation, ...], None
            else:
                # self.v_kwargs_name = name
                fields[p.name] = dict[str, annotation], None  # type: ignore[valid-type]
        # these checks avoid a clash between "args" and a field with that name
        if not self.takes_args and self.v_args_name in fields:
            self.v_args_name = ALT_V_ARGS
        # same with "kwargs"
        if not self.takes_kwargs and self.v_kwargs_name in fields:
            self.v_kwargs_name = ALT_V_KWARGS
        if not self.takes_args:
            # we add the field so validation below can raise the correct exception
            fields[self.v_args_name] = List[Any], None
        if not self.takes_kwargs:
            # same with kwargs
            fields[self.v_kwargs_name] = Dict[Any, Any], None
        return fields

    @field_validator("parameters", mode="before")
    @classmethod
    def listify(cls, params: Mapping[str, _Parameter]) -> Collection[_Parameter]:
        return params.values()

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

    @property
    def positional_only_args(self) -> set[str]:
        return {p.name for p in self.parameters if p.is_positional_only}


# class _ParameterKind(IntEnum):
#     POSITIONAL_ONLY = 0
#     POSITIONAL_OR_KEYWORD = 1
#     VAR_POSITIONAL = 2
#     KEYWORD_ONLY = 3
#     VAR_KEYWORD = 4
