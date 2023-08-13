import typing

__all__ = ["add_json_schema", "add_fields"]

add_json_schema = {
    "properties": {
        "a": {"title": "A", "type": "integer"},
        "v__duplicate_kwargs": {
            "default": None,
            "items": {"type": "string"},
            "title": "V  Duplicate Kwargs",
            "type": "array",
        },
        "b": {"title": "B", "type": "integer"},
        "args": {"default": None, "items": {}, "title": "Args", "type": "array"},
        "kwargs": {"default": None, "title": "Kwargs", "type": "object"},
    },
    "required": ["a", "b"],
    "title": "Add",
    "type": "object",
}

add_fields = {
    "a": (int, ...),
    "args": (typing.List[typing.Any], None),
    "b": (int, ...),
    "kwargs": (typing.Dict[typing.Any, typing.Any], None),
    "v__duplicate_kwargs": (typing.List[str], None),
}
