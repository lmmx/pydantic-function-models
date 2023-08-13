import sys
from inspect import Parameter, signature
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    get_type_hints,
)

from pydantic.alias_generators import to_pascal
from pydantic.errors import PydanticUserError
from pydantic.functional_validators import field_validator
from pydantic.main import BaseModel, create_model

__all__ = ["ValidatedFunction"]

assert sys.version_info >= (3, 10), "typing.get_type_hints needs Python 3.10+"

if TYPE_CHECKING:
    AnyCallable = Callable[..., Any]

    AnyCallableT = TypeVar("AnyCallableT", bound=AnyCallable)


ALT_V_ARGS = "v__args"
ALT_V_KWARGS = "v__kwargs"
V_POSITIONAL_ONLY_NAME = "v__positional_only"
V_DUPLICATE_KWARGS = "v__duplicate_kwargs"


class ValidatedFunction:
    def __init__(self, function: "AnyCallable"):
        parameters: Mapping[str, Parameter] = signature(function).parameters

        if parameters.keys() & {
            ALT_V_ARGS,
            ALT_V_KWARGS,
            V_POSITIONAL_ONLY_NAME,
            V_DUPLICATE_KWARGS,
        }:
            raise PydanticUserError(
                f'"{ALT_V_ARGS}", "{ALT_V_KWARGS}", "{V_POSITIONAL_ONLY_NAME}" and "{V_DUPLICATE_KWARGS}" '
                "are not permitted as argument names when using the ValidatedFunction wrapper",
                code=None,
            )

        self.raw_function = function
        self.arg_mapping: dict[int, str] = {}
        self.positional_only_args: set[str] = set()
        self.v_args_name = "args"
        self.v_kwargs_name = "kwargs"

        type_hints = get_type_hints(function, include_extras=True)
        takes_args = False
        takes_kwargs = False
        fields: dict[str, tuple[Any, Any]] = {}
        for i, (name, p) in enumerate(parameters.items()):
            if p.annotation is p.empty:
                annotation = Any
            else:
                annotation = type_hints[name]

            default = ... if p.default is p.empty else p.default
            if p.kind == Parameter.POSITIONAL_ONLY:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_POSITIONAL_ONLY_NAME] = List[str], None
                self.positional_only_args.add(name)
            elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_DUPLICATE_KWARGS] = List[str], None
            elif p.kind == Parameter.KEYWORD_ONLY:
                fields[name] = annotation, default
            elif p.kind == Parameter.VAR_POSITIONAL:
                self.v_args_name = name
                fields[name] = Tuple[annotation, ...], None
                takes_args = True
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                self.v_kwargs_name = name
                fields[name] = dict[str, annotation], None  # type: ignore[valid-type]
                takes_kwargs = True

        # these checks avoid a clash between "args" and a field with that name
        if not takes_args and self.v_args_name in fields:
            self.v_args_name = ALT_V_ARGS

        # same with "kwargs"
        if not takes_kwargs and self.v_kwargs_name in fields:
            self.v_kwargs_name = ALT_V_KWARGS

        if not takes_args:
            # we add the field so validation below can raise the correct exception
            fields[self.v_args_name] = List[Any], None

        if not takes_kwargs:
            # same with kwargs
            fields[self.v_kwargs_name] = Dict[Any, Any], None

        self.create_model(fields, takes_args, takes_kwargs)

    def init_model_instance(self, *args: Any, **kwargs: Any) -> BaseModel:
        values = self.build_values(args, kwargs)
        return self.model(**values)

    def call(self, *args: Any, **kwargs: Any) -> Any:
        m = self.init_model_instance(*args, **kwargs)
        return self.execute(m)

    def build_values(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if args:
            arg_iter = enumerate(args)
            while True:
                try:
                    i, a = next(arg_iter)
                except StopIteration:
                    break
                arg_name = self.arg_mapping.get(i)
                if arg_name is not None:
                    values[arg_name] = a
                else:
                    values[self.v_args_name] = [a] + [a for _, a in arg_iter]
                    break

        var_kwargs: dict[str, Any] = {}
        wrong_positional_args = []
        duplicate_kwargs = []
        fields_alias = [
            field.alias
            for name, field in self.model.model_fields.items()
            if name not in (self.v_args_name, self.v_kwargs_name)
        ]
        non_var_fields = set(self.model.model_fields) - {
            self.v_args_name,
            self.v_kwargs_name,
        }
        for k, v in kwargs.items():
            if k in non_var_fields or k in fields_alias:
                if k in self.positional_only_args:
                    wrong_positional_args.append(k)
                if k in values:
                    duplicate_kwargs.append(k)
                values[k] = v
            else:
                var_kwargs[k] = v

        if var_kwargs:
            values[self.v_kwargs_name] = var_kwargs
        if wrong_positional_args:
            values[V_POSITIONAL_ONLY_NAME] = wrong_positional_args
        if duplicate_kwargs:
            values[V_DUPLICATE_KWARGS] = duplicate_kwargs
        return values

    def execute(self, m: BaseModel) -> Any:
        d = {
            k: v
            for k, v in m.__dict__.items()
            if k in m.__pydantic_fields_set__ or m.model_fields[k].default_factory
        }
        var_kwargs = d.pop(self.v_kwargs_name, {})

        if self.v_args_name in d:
            args_: list[Any] = []
            in_kwargs = False
            kwargs = {}
            for name, value in d.items():
                if in_kwargs:
                    kwargs[name] = value
                elif name == self.v_args_name:
                    args_ += value
                    in_kwargs = True
                else:
                    args_.append(value)
            return self.raw_function(*args_, **kwargs, **var_kwargs)
        elif self.positional_only_args:
            args_ = []
            kwargs = {}
            for name, value in d.items():
                if name in self.positional_only_args:
                    args_.append(value)
                else:
                    kwargs[name] = value
            return self.raw_function(*args_, **kwargs, **var_kwargs)
        else:
            return self.raw_function(**d, **var_kwargs)

    def create_model(
        self,
        fields: dict[str, Any],
        takes_args: bool,
        takes_kwargs: bool,
    ) -> None:
        pos_args = len(self.arg_mapping)

        class DecoratorBaseModel(BaseModel):
            @field_validator(self.v_args_name, check_fields=False)
            @classmethod
            def check_args(cls, v: Optional[List[Any]]) -> Optional[List[Any]]:
                if takes_args or v is None:
                    return v

                raise TypeError(
                    f"{pos_args} positional arguments expected but {pos_args + len(v)} given",
                )

            @field_validator(self.v_kwargs_name, check_fields=False)
            @classmethod
            def check_kwargs(
                cls,
                v: Optional[Dict[str, Any]],
            ) -> Optional[Dict[str, Any]]:
                if takes_kwargs or v is None:
                    return v

                plural = "" if len(v) == 1 else "s"
                keys = ", ".join(map(repr, v.keys()))
                raise TypeError(f"unexpected keyword argument{plural}: {keys}")

            @field_validator(V_POSITIONAL_ONLY_NAME, check_fields=False)
            @classmethod
            def check_positional_only(cls, v: Optional[List[str]]) -> None:
                if v is None:
                    return

                plural = "" if len(v) == 1 else "s"
                keys = ", ".join(map(repr, v))
                raise TypeError(
                    f"positional-only argument{plural} passed as keyword argument{plural}: {keys}",
                )

            @field_validator(V_DUPLICATE_KWARGS, check_fields=False)
            @classmethod
            def check_duplicate_kwargs(cls, v: Optional[List[str]]) -> None:
                if v is None:
                    return

                plural = "" if len(v) == 1 else "s"
                keys = ", ".join(map(repr, v))
                raise TypeError(f"multiple values for argument{plural}: {keys}")

        self.model = create_model(
            to_pascal(self.raw_function.__name__),
            __base__=DecoratorBaseModel,
            **fields,
        )
